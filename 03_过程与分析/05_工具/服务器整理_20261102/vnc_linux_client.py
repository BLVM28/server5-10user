"""Standard VNC client for the authorised Linux session, not Windows automation.

Credentials are read interactively and never written to disk. Shared=True keeps
the existing RealVNC viewer connected. JSON commands arrive over stdin.
"""
import getpass
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "vnc_client_deps"))
from vncdotool import api
from vncdotool.client import VNCDoToolFactory, VNCDoToolClient
from vncdotool import rfb


class CompressedClient(VNCDoToolClient):
    encoding = rfb.Encoding.HEXTILE

    def clientCutText(self, message):
        super().clientCutText(message)
        return self


class SharedFactory(VNCDoToolFactory):
    shared = True
    protocol = CompressedClient


def main():
    password = getpass.getpass("VNC password (not saved): ")
    client = api.connect("ic5h22.nicu.cn::15910", password=password,
                         factory_class=SharedFactory, timeout=25)
    password = None
    try:
        first = HERE / "vnc_direct_initial.png"
        client.captureScreen(str(first))
        print(json.dumps({"ready": True, "capture": str(first)}), flush=True)
        for line in sys.stdin:
            try:
                request = json.loads(line)
                operation = request["op"]
                if operation == "quit":
                    break
                if operation == "key":
                    client.keyPress(request["key"])
                elif operation in ("type", "command"):
                    text = request["text"]
                    if not text.isascii() or "\n" in text or "\r" in text:
                        raise ValueError("type requires one ASCII line")
                    if operation == "command":
                        client.keyPress("ctrl-u")
                    for character in text:
                        client.keyPress(character)
                        time.sleep(0.001)
                    if operation == "command":
                        client.keyPress("enter")
                elif operation == "paste_command":
                    text = request["text"]
                    if not text.isascii() or "\n" in text or "\r" in text:
                        raise ValueError("paste_command requires one ASCII line")
                    client.keyPress("ctrl-u")
                    client.clientCutText(text)
                    time.sleep(0.3)
                    client.keyPress("ctrl-shift-v")
                    time.sleep(0.3)
                    if request.get("execute", False):
                        client.keyPress("enter")
                elif operation == "capture":
                    pass
                else:
                    raise ValueError("unsupported operation")
                time.sleep(min(float(request.get("wait", 0.4)), 30))
                destination = HERE / request.get("capture", "vnc_direct_latest.png")
                if destination.parent.resolve() != HERE:
                    raise ValueError("capture path must remain in this directory")
                client.captureScreen(str(destination))
                print(json.dumps({"ok": True, "capture": str(destination)}), flush=True)
            except Exception as error:
                print(json.dumps({"ok": False, "error": str(error)}), flush=True)
    finally:
        if client.protocol is not None:
            api.reactor.callFromThread(client.protocol.transport.loseConnection)
        api.shutdown()


if __name__ == "__main__":
    main()
