from typing import List, Dict
from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
import os
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from dotenv import load_dotenv

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"


class FileAnalysis(BaseModel):
    """개별 파일에 대한 분석 결과."""

    file_path: str = Field(description="분석된 파일의 상대 경로")
    file_type: str = Field(
        description="파일의 타입 (예: Python, JavaScript, TypeScript, etc.)"
    )
    purpose: str = Field(description="파일의 주요 목적과 기능")
    key_components: List[str] = Field(
        default_factory=list, description="파일 내 주요 클래스, 함수, 컴포넌트 목록"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="파일이 의존하는 외부 모듈이나 라이브러리"
    )
    complexity_score: int = Field(description="파일의 복잡도 점수 (1-10)", ge=1, le=10)


class DirectoryStructure(BaseModel):
    """디렉토리 구조 분석 결과."""

    directory_path: str = Field(description="분석된 디렉토리 경로")
    subdirectories: List[str] = Field(
        default_factory=list, description="하위 디렉토리 목록"
    )
    files: List[str] = Field(default_factory=list, description="파일 목록")
    total_files: int = Field(description="총 파일 개수")
    file_types_distribution: Dict[str, int] = Field(
        default_factory=dict, description="파일 타입별 분포"
    )


class ProjectAnalysis(BaseModel):
    """전체 프로젝트 분석 결과."""

    project_name: str = Field(description="프로젝트 이름")
    root_directory: str = Field(description="루트 디렉토리 경로")
    project_type: str = Field(
        description="프로젝트 유형 (web app, API server, library, etc.)"
    )
    main_purpose: str = Field(description="프로젝트의 주요 목적과 기능")
    architecture_pattern: str = Field(description="사용된 아키텍처 패턴")
    key_technologies: List[str] = Field(
        default_factory=list, description="사용된 주요 기술 스택"
    )
    directory_structure: DirectoryStructure = Field(description="디렉토리 구조")
    file_analyses: List[FileAnalysis] = Field(
        default_factory=list, description="개별 파일 분석 결과"
    )
    dependencies_summary: Dict[str, List[str]] = Field(
        default_factory=dict, description="의존성 요약"
    )
    design_patterns: List[str] = Field(
        default_factory=list, description="발견된 디자인 패턴"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="개선 제안사항"
    )


class CodeAnalysisRequest(BaseModel):
    """코드 분석 요청 모델."""

    target_directory: str = Field(description="분석할 디렉토리의 절대 경로")
    analysis_depth: int = Field(
        default=3, description="분석할 디렉토리 깊이", ge=1, le=10
    )
    include_patterns: List[str] = Field(
        default_factory=lambda: [
            "*.py",
            "*.js",
            "*.ts",
            "*.jsx",
            "*.tsx",
            "*.java",
            "*.cpp",
            "*.c",
            "*.h",
        ],
        description="포함할 파일 패턴",
    )
    exclude_patterns: List[str] = Field(
        default_factory=lambda: [
            "node_modules",
            "__pycache__",
            ".git",
            "*.pyc",
            "*.log",
        ],
        description="제외할 파일/디렉토리 패턴",
    )


# 코드 분석 Agent 정의
code_analysis_agent = LlmAgent(
    model=GEMINI_MODEL,
    name="CodeAnalysisAgent",
    description="디렉토리의 코드 파일들을 분석하여 구조, 의존성, 설계 의도 등을 파악합니다.",
    instruction="""
당신은 숙련된 코드 리뷰어이자 소프트웨어 아키텍트입니다. 다음 지침에 따라 주어진 디렉토리를 종합적으로 분석하고, 그 결과를 명확하고 실용적인 마크다운 문서로 정리해 주세요.

**분석 및 문서화 지침:**

1.  **핵심 파악**:
    * **프로젝트 개요**: 디렉토리 구조, 파일 분포, 프로젝트 유형, 전반적인 목적 및 기능.
    * **코드 심층 분석**: 각 파일의 핵심 목적, 주요 기능, 클래스/함수/컴포넌트 식별, 외부 의존성 및 코드 복잡도.
    * **설계 및 기술 스택**: 아키텍처/디자인 패턴, 사용된 기술 스택, 주요 의존성 관계.

2.  **문서화**:
    * 분석 결과를 바탕으로 **`__analysis__`** 디렉토리 내에 다음 마크다운 문서를 생성합니다:
        * `README.md` (프로젝트 개요)
        * `architecture.md` (아키텍처 및 설계)
        * `dependencies.md` (의존성 분석)
        * `[file_name]_analysis.md` (개별 파일 상세)
        * `recommendations.md` (개선 제안)

3.  **핵심 역량 발휘**:
    * 코드 품질과 설계 패턴을 객관적으로 평가합니다.
    * 실용적이고 구체적인 개선 제안을 제시합니다.
    * 프로젝트의 비즈니스 목적을 고려하여 분석합니다.
    """,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    # 동적으로 디렉토리 경로가 설정됨
                    "/",  # 루트부터 접근 가능하도록 설정
                ],
            ),
        )
    ],
)


# 분석 실행을 위한 헬퍼 함수
def analyze_directory(directory_path: str, analysis_depth: int = 3) -> str:
    """
    디렉토리 분석을 실행하는 헬퍼 함수

    Args:
        directory_path: 분석할 디렉토리의 절대 경로
        analysis_depth: 분석할 디렉토리 깊이

    Returns:
        분석 결과 메시지
    """
    if not os.path.exists(directory_path):
        return f"오류: 디렉토리 '{directory_path}'가 존재하지 않습니다."

    if not os.path.isdir(directory_path):
        return f"오류: '{directory_path}'는 디렉토리가 아닙니다."

    # 분석 요청 생성
    CodeAnalysisRequest(target_directory=directory_path, analysis_depth=analysis_depth)

    # Agent 실행을 위한 프롬프트 생성
    prompt = f"""
    다음 디렉토리를 분석해주세요:

    **대상 디렉토리**: {directory_path}
    **분석 깊이**: {analysis_depth}

    분석 완료 후 `{directory_path}/__analysis__` 디렉토리에 분석 결과 문서들을 생성해주세요.

    생성할 문서:
    1. README.md - 프로젝트 전체 개요
    2. architecture.md - 아키텍처 설계 분석  
    3. dependencies.md - 의존성 분석
    4. [file_name]_analysis.md - 개별 파일 상세 분석
    5. recommendations.md - 개선 제안사항
    """

    return prompt


# ADK 호환성을 위한 루트 에이전트
root_agent = code_analysis_agent

# 사용 예시
if __name__ == "__main__":
    # 예시 사용법
    target_directory = "/path/to/your/project"
    analysis_prompt = analyze_directory(target_directory)
    print("분석 프롬프트 생성 완료:")
    print(analysis_prompt)
