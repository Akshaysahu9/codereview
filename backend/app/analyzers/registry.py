from app.analyzers.cpp_analyzer import CppAnalyzer
from app.analyzers.java_analyzer import JavaAnalyzer
from app.analyzers.javascript_analyzer import JavaScriptAnalyzer, TypeScriptAnalyzer
from app.analyzers.python_analyzer import PythonAnalyzer
from app.schemas import Language

ANALYZERS = {
    Language.PYTHON: PythonAnalyzer(),
    Language.JAVASCRIPT: JavaScriptAnalyzer(),
    Language.TYPESCRIPT: TypeScriptAnalyzer(),
    Language.JAVA: JavaAnalyzer(),
    Language.CPP: CppAnalyzer(),
}


def get_analyzer(language: Language):
    return ANALYZERS[language]
