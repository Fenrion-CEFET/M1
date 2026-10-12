"""
FENRION - Missao 1 "Bouncing 2.0" - teste de visao em bancada

Detecta, em cada quadro:
  - marcador ArUco (ID) e o gabarito (forma que contem o ArUco)
  - bases de pouso: forma (triangulo, hexagono, estrela) + numero (3, 4 ou 5)
  - base correta: mesma forma do gabarito e numero que divide o ID

Fontes de imagem:
  python m1_visao.py --url http://192.168.0.50:81/stream   (stream da ESP32-S3)
  python m1_visao.py --cap http://192.168.0.50/capture     (fotos uma a uma)
  python m1_visao.py --cam 0                               (webcam do PC)
  python m1_visao.py --img foto.jpg                        (imagem parada)

Teclas na janela: q = sair, s = salvar quadro, d = mostrar imagem binarizada
"""

import argparse
import time

import cv2
import numpy as np

# ===================== Ajustes =====================
ARUCO_DICTS = [  # testados em ordem ate achar um marcador; troque se souber o do regulamento
    "DICT_4X4_50", "DICT_4X4_100", "DICT_5X5_50", "DICT_5X5_100",
    "DICT_6X6_50", "DICT_6X6_250", "DICT_ARUCO_ORIGINAL",
]
MIN_AREA_FRAC = 0.002   # area minima de uma forma (fracao da imagem)
MAX_AREA_FRAC = 0.25    # area maxima
ADAPT_BLOCK = 31        # janela do limiar adaptativo (impar)
ADAPT_C = 10            # quanto mais alto, menos ruido (e menos detalhe)
DIGITS = (3, 4, 5)


# ===================== ArUco =====================
class ArucoFinder:
    def __init__(self, names):
        self.detectors = []
        for n in names:
            d = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, n))
            p = cv2.aruco.DetectorParameters()
            self.detectors.append((n, cv2.aruco.ArucoDetector(d, p)))
        self.locked = None  # dicionario que funcionou, usado primeiro nas proximas vezes

    def find(self, gray):
        order = self.detectors
        if self.locked is not None:
            order = [self.locked] + [x for x in self.detectors if x is not self.locked]
        for item in order:
            corners, ids, _ = item[1].detectMarkers(gray)
            if ids is not None and len(ids):
                self.locked = item
                c = np.asarray(corners[0]).reshape(4, 2)
                # OpenCV 4 devolve ids como Nx1, OpenCV 5 como N: flatten serve para os dois
                return int(np.asarray(ids).flatten()[0]), c, item[0]
        return None


# ===================== Formas =====================
def classify_shape(cnt):
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)
    v = len(approx)
    area = cv2.contourArea(cnt)
    hull_area = cv2.contourArea(cv2.convexHull(cnt))
    solidity = area / hull_area if hull_area > 0 else 0
    if solidity < 0.75 and 8 <= v <= 12:
        return "estrela"
    if solidity > 0.85:
        if v == 3:
            return "triangulo"
        if v == 6:
            return "hexagono"
        if v == 4:
            return "quadrado"
    return None


def find_shapes(binary, img_area):
    cnts, hier = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    shapes = []
    for c in cnts:
        a = cv2.contourArea(c)
        if a < MIN_AREA_FRAC * img_area or a > MAX_AREA_FRAC * img_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        H, W = binary.shape
        if x <= 2 or y <= 2 or x + w >= W - 2 or y + h >= H - 2:
            continue  # forma cortada pela borda da imagem: ignora ate aparecer inteira
        kind = classify_shape(c)
        if kind is None:
            continue
        m = cv2.moments(c)
        cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
        # contornos de borda (externo/interno do traco) geram duplicatas: fica o maior
        dup = None
        for s in shapes:
            if s["kind"] == kind and np.hypot(s["c"][0] - cx, s["c"][1] - cy) < 0.15 * np.sqrt(a):
                dup = s
                break
        if dup:
            if a > dup["area"]:
                dup.update(cnt=c, area=a, c=(cx, cy))
            continue
        shapes.append({"kind": kind, "cnt": c, "area": a, "c": (cx, cy), "digit": None, "score": 0})
    return shapes


# ===================== Digitos =====================
def make_templates():
    """Gera modelos dos digitos 3, 4, 5 em fontes do OpenCV."""
    temps = {}
    for d in DIGITS:
        lst = []
        for font in (cv2.FONT_HERSHEY_SIMPLEX, cv2.FONT_HERSHEY_DUPLEX):
            for th in (6, 10):
                canvas = np.zeros((140, 140), np.uint8)
                cv2.putText(canvas, str(d), (25, 115), font, 4, 255, th, cv2.LINE_AA)
                lst.append(normalize_glyph(canvas))
        temps[d] = lst
    return temps


def normalize_glyph(bw, size=(32, 48)):
    ys, xs = np.nonzero(bw > 127)
    if len(xs) < 10:
        return None
    g = bw[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    g = cv2.resize(g, size, interpolation=cv2.INTER_AREA)
    return (g > 127).astype(np.float32)


def glyph_score(a, b):
    inter = np.sum(a * b)
    union = np.sum(np.maximum(a, b))
    return inter / union if union else 0


def read_digit(binary, shape, templates):
    """Le o numero dentro da forma, testando rotacoes (o drone pode estar girado)."""
    x, y, w, h = cv2.boundingRect(shape["cnt"])
    mask = np.zeros(binary.shape, np.uint8)
    cv2.drawContours(mask, [shape["cnt"]], -1, 255, -1)
    # encolhe a mascara para descartar o traco da propria forma
    k = max(3, int(0.12 * min(w, h)) | 1)
    mask = cv2.erode(mask, np.ones((k, k), np.uint8))
    inner = cv2.bitwise_and(binary, mask)[y:y + h, x:x + w]
    cnts, _ = cv2.findContours(inner, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None, 0
    # o digito e o maior blob perto do centro
    c = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(c) < 0.01 * w * h:
        return None, 0
    blob = np.zeros_like(inner)
    cv2.drawContours(blob, [c], -1, 255, -1)
    blob = cv2.bitwise_and(inner, blob)
    side = int(1.5 * max(blob.shape))
    pad = np.zeros((side, side), np.uint8)
    oy, ox = (side - blob.shape[0]) // 2, (side - blob.shape[1]) // 2
    pad[oy:oy + blob.shape[0], ox:ox + blob.shape[1]] = blob

    best_d, best_s = None, 0
    for ang in range(0, 360, 15):
        M = cv2.getRotationMatrix2D((side / 2, side / 2), ang, 1.0)
        g = normalize_glyph(cv2.warpAffine(pad, M, (side, side)))
        if g is None:
            continue
        for d, lst in templates.items():
            for t in lst:
                s = glyph_score(g, t)
                if s > best_s:
                    best_d, best_s = d, s
    return (best_d, best_s) if best_s > 0.45 else (None, best_s)


# ===================== Decisao =====================
def point_in(cnt, pt):
    return cv2.pointPolygonTest(cnt, (float(pt[0]), float(pt[1])), False) >= 0


def decide(aruco, shapes):
    """Retorna (gabarito, base_correta, mensagem)."""
    if aruco is None:
        return None, None, "procurando ArUco..."
    mid, corners, _ = aruco
    ac = corners.mean(axis=0)
    gab = None
    for s in shapes:
        if s["kind"] in ("triangulo", "hexagono", "estrela") and point_in(s["cnt"], ac):
            if gab is None or s["area"] > gab["area"]:
                gab = s
    if gab is None:
        return None, None, f"ArUco ID {mid}: forma do gabarito nao identificada"
    divisores = [d for d in DIGITS if mid % d == 0]
    if not divisores:
        return gab, None, f"ID {mid} ({gab['kind']}): nenhum de 3/4/5 divide o ID"
    msg = f"ID {mid} | gabarito {gab['kind']} | divisores {divisores}"
    if len(divisores) > 1:
        msg += " | ATENCAO: ID ambiguo"
    cands = [s for s in shapes if s is not gab and s["kind"] == gab["kind"] and s["digit"] in divisores]
    if not cands:
        return gab, None, msg + " | base ainda nao vista"
    alvo = max(cands, key=lambda s: s["score"])
    return gab, alvo, msg + f" | POUSAR: {alvo['kind']} {alvo['digit']}"


# ===================== Processamento de um quadro =====================
def process(frame, aruco_finder, templates):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    binary = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, ADAPT_BLOCK, ADAPT_C)
    h, w = gray.shape
    aruco = aruco_finder.find(gray)
    shapes = find_shapes(binary, h * w)

    # apaga a regiao do ArUco antes de ler digitos (evita confundir com o marcador)
    bin_dig = binary.copy()
    if aruco is not None:
        cv2.fillPoly(bin_dig, [aruco[1].astype(np.int32)], 0)
    for s in shapes:
        if s["kind"] != "quadrado":
            s["digit"], s["score"] = read_digit(bin_dig, s, templates)

    gab, alvo, msg = decide(aruco, shapes)

    # ---------- desenho ----------
    out = frame.copy()
    if aruco is not None:
        cv2.polylines(out, [aruco[1].astype(np.int32)], True, (255, 0, 255), 2)
        cv2.putText(out, f"ID {aruco[0]} ({aruco[2]})", tuple(aruco[1][0].astype(int) + [0, -8]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
    for s in shapes:
        if s["kind"] == "quadrado":
            continue
        color = (0, 200, 255)
        if s is gab:
            color = (255, 0, 255)
        if s is alvo:
            color = (0, 255, 0)
        cv2.drawContours(out, [s["cnt"]], -1, color, 2)
        label = s["kind"] + (f" {s['digit']}" if s["digit"] else "")
        cx, cy = int(s["c"][0]), int(s["c"][1])
        cv2.putText(out, label, (cx - 40, cy + int(np.sqrt(s["area"]) * 0.7)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    if alvo is not None:
        # erro do alvo em relacao ao centro da imagem (base para o controle de pouso)
        ex = (alvo["c"][0] - w / 2) / (w / 2)
        ey = (alvo["c"][1] - h / 2) / (h / 2)
        cv2.line(out, (w // 2, h // 2), (int(alvo["c"][0]), int(alvo["c"][1])), (0, 255, 0), 2)
        msg += f" | erro x={ex:+.2f} y={ey:+.2f}"
    cv2.drawMarker(out, (w // 2, h // 2), (255, 255, 255), cv2.MARKER_CROSS, 20, 1)

    cv2.rectangle(out, (0, 0), (w, 26), (0, 0, 0), -1)
    cv2.putText(out, msg, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return out, binary, msg


# ===================== Fontes de imagem =====================
class CaptureSource:
    """Busca fotos no /capture da ESP32 (mais lento, mas funciona em qualquer resolucao)."""
    def __init__(self, url):
        import requests
        self.url, self.req = url, requests

    def read(self):
        try:
            r = self.req.get(self.url, timeout=5)
            img = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
            return img is not None, img
        except Exception as e:
            print("Falha no /capture:", e)
            time.sleep(1)
            return False, None


def config_path():
    """Arquivo de configuracao ao lado do script (ou do .exe)."""
    import os
    import sys
    base = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
    return os.path.join(base, "m1_config.txt")


def ask_source(args):
    """Sem argumentos (dois cliques no .exe): pergunta a fonte e lembra a ultima usada."""
    last = ""
    try:
        with open(config_path(), encoding="utf-8") as f:
            last = f.read().strip()
    except OSError:
        pass
    print("=== FENRION M1 - visao ===")
    print("Digite o IP da camera ESP32-S3 (ex: 192.168.0.50)")
    print("  w = webcam do PC   |   Enter = usar o ultimo" + (f" ({last})" if last else ""))
    resp = input("> ").strip() or last
    if not resp:
        raise SystemExit("Nenhuma fonte informada.")
    try:
        with open(config_path(), "w", encoding="utf-8") as f:
            f.write(resp)
    except OSError:
        pass
    if resp.lower() == "w":
        args.cam = 0
    elif resp.startswith("http"):
        args.url = resp
    else:
        args.url = f"http://{resp}:81/stream"
    print("Abrindo", args.url if args.url else "webcam", "... (q na janela da imagem para sair)")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=False)
    g.add_argument("--url", help="stream MJPEG, ex: http://IP:81/stream")
    g.add_argument("--cap", help="captura unica, ex: http://IP/capture")
    g.add_argument("--cam", type=int, help="indice da webcam")
    g.add_argument("--img", help="arquivo de imagem")
    ap.add_argument("--save", help="salvar o resultado (somente com --img)")
    args = ap.parse_args()
    if not (args.url or args.cap or args.img or args.cam is not None):
        ask_source(args)

    finder = ArucoFinder(ARUCO_DICTS)
    templates = make_templates()

    if args.img:
        frame = cv2.imread(args.img)
        if frame is None:
            raise SystemExit("Nao consegui abrir " + args.img)
        out, binary, msg = process(frame, finder, templates)
        print(msg)
        if args.save:
            cv2.imwrite(args.save, out)
        else:
            cv2.imshow("M1 visao", out)
            cv2.waitKey(0)
        return

    if args.cap:
        src = CaptureSource(args.cap)
    else:
        src = cv2.VideoCapture(args.url if args.url else args.cam)
        if not src.isOpened():
            raise SystemExit("Nao consegui abrir a fonte de video")

    show_bin, last_msg, n = False, "", 0
    t0 = time.time()
    while True:
        ok, frame = src.read()
        if not ok:
            continue
        out, binary, msg = process(frame, finder, templates)
        n += 1
        fps = n / (time.time() - t0)
        cv2.putText(out, f"{fps:.1f} fps", (6, out.shape[0] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        if msg != last_msg:
            print(msg)
            last_msg = msg
        cv2.imshow("M1 visao", binary if show_bin else out)
        k = cv2.waitKey(1) & 0xFF
        if k == ord("q"):
            break
        if k == ord("d"):
            show_bin = not show_bin
        if k == ord("s"):
            name = time.strftime("m1_%H%M%S.jpg")
            cv2.imwrite(name, frame)
            print("salvo", name)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    import sys
    try:
        main()
    except SystemExit as e:
        if e.code not in (None, 0):
            print("\nERRO:", e.code)
            if len(sys.argv) == 1:
                input("Pressione Enter para fechar...")
    except Exception:
        import traceback
        traceback.print_exc()
        if len(sys.argv) == 1:
            input("\nPressione Enter para fechar...")
