"""Deprecated no-browser backend placeholder.

The current Macaulay Library search flow requires its browser verification.
Use QuizBackend for live searches or QuizBackend(from_file=True) for local images.
"""


class QuizBackendNoWeb:
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "QuizBackendNoWeb is retired. Use QuizBackend for browser-backed "
            "searches or the local-file mode for offline quizzes."
        )
