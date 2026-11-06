import requests


class LLMError(Exception):
    """Ошибка при обращении к модели."""


class OllamaClient:
    def __init__(
        self,
        model="gemma3:4b",
        host="http://localhost:11434",
        timeout=180,
        temperature=0.2,
        seed=None,
    ):
        self.model = model
        self.host = host
        self.timeout = timeout
        self.temperature = temperature
        self.seed = seed

    def chat(self, system: str, user: str) -> str:
        options = {"temperature": self.temperature, "num_predict": 700}
        if self.seed is not None:
            options["seed"] = self.seed
        payload = {
            "model": self.model,
            "stream": False,
            "options": options,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            resp = requests.post(
                f"{self.host}/api/chat", json=payload, timeout=self.timeout
            )
        except requests.exceptions.ConnectionError:
            raise LLMError(
                "Ollama не отвечает. Запусти приложение Ollama и повтори."
            )
        except requests.exceptions.Timeout:
            raise LLMError("Модель не ответила вовремя. Попробуй ещё раз.")
        except requests.RequestException as err:
            raise LLMError(f"Ошибка запроса: {err}")

        if resp.status_code == 404:
            raise LLMError(
                f"Модель {self.model} не найдена. Выполни: ollama pull {self.model}"
            )
        if resp.status_code != 200:
            raise LLMError(f"Ollama вернула код {resp.status_code}")

        return resp.json()["message"]["content"].strip()