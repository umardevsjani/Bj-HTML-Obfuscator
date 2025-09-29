import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
import html
import re

app = FastAPI()

def obfuscate_html(
    icode: str,
    removeScript: bool = True,
    removeComment: bool = True,
) -> str:
    if not isinstance(icode, str):
        raise TypeError("icode must be a string")

    form_body = {
        "cmd": "obfuscate",
        "icode": icode,
        "remove-script": "y" if removeScript else "n",
        "remove-comment": "y" if removeComment else "n",
        "ocode": "",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://www.phpkobo.com",
        "referer": "https://www.phpkobo.com/html-obfuscator",
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
    }

    try:
        resp = requests.post("https://www.phpkobo.com/html-obfuscator", data=form_body, headers=headers)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch response from phpkobo.com: {str(e)}")

    soup = BeautifulSoup(resp.text, "html.parser")
    textarea = soup.select_one("textarea.codebox-input[name=ocode]")

    if textarea:
        text = textarea.get_text().strip()
        if not text:
            # Fallback to value attribute
            text = textarea.get("value", "").strip()

        if text:
            # Decode Unicode escape sequences (e.g., \u003C to <)
            text = html.unescape(text)
            # Remove unwanted comments (e.g., <!-- Obfuscated at ... -->)
            text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
            # Remove any stray <script> tags if removeScript is True
            if removeScript:
                text = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", text, flags=re.DOTALL)
            return text.strip()

    raise ValueError("Failed to extract obfuscated HTML from the response.")

@app.get("/obfuscate")
async def obfuscate(code: str, removeScript: bool = True, removeComment: bool = True):
    try:
        obfuscated_code = obfuscate_html(code, removeScript, removeComment)
        return {"obfuscated_code": obfuscated_code}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
