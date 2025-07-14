from typing import List, Literal
from google.adk.agents import LlmAgent, SequentialAgent
from pydantic import BaseModel, Field
import os
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

GEMINI_MODEL = "gemini-2.5-flash"
TARGET_FOLDER_PATH = os.environ['TARGET_FOLDER_PATH']

class ComponentDetail(BaseModel):
    """개별 컴포넌트 또는 기능에 대한 상세 정보."""
    name: str = Field(description="컴포넌트 또는 기능의 이름 (예: LoginPage, ProductCard, UserAuthAPI)")
    description: str = Field(description="컴포넌트 또는 기능에 대한 간략한 설명")
    type: Literal["frontend_page", "frontend_component", "backend_api", "backend_model", "utility"] = Field(
        description="컴포넌트 또는 기능의 유형"
    )
    dependencies: List[str] = Field(default_factory=list, description="이 컴포넌트/기능이 의존하는 다른 컴포넌트/기능 목록")


class CodeGenerationPlan(BaseModel):
    """전체 코드 생성 프로젝트에 대한 상세 계획."""
    project_name: str = Field(description="프로젝트의 이름")
    overall_description: str = Field(description="프로젝트에 대한 전반적인 설명")
    frontend_pages: List[ComponentDetail] = Field(default_factory=list, description="생성할 프론트엔드 페이지 목록")
    common_components: List[ComponentDetail] = Field(default_factory=list, description="생성할 공통 UI 컴포넌트 목록")
    core_logic: List[ComponentDetail] = Field(default_factory=list, description="코어 로직 또는 유틸리티 목록")
    integration_steps: List[str] = Field(default_factory=list, description="생성된 코드 통합을 위한 단계 목록")


class GeneratedCode(BaseModel):
    """에이전트가 생성한 코드 조각."""
    file_name: str = Field(description="생성된 코드의 파일 이름 (예: LoginPage.jsx, Button.tsx, users.py)")
    language: str = Field(description="코드의 프로그래밍 언어 (예: javascript, python, html, css)")
    code_content: str = Field(description="생성된 코드의 실제 내용")
    description: str = Field(description="생성된 코드에 대한 간략한 설명")


class CodeGenerationRequest(BaseModel):
    """코드 생성을 위한 서브 모듈 에이전트 요청 모델."""
    component_details: List[ComponentDetail] = Field(description="생성할 컴포넌트/기능의 상세 목록")
    overall_context: str = Field(description="전체 프로젝트에 대한 일반적인 컨텍스트")


class CodeGenerationResponse(BaseModel):
    """서브 모듈 에이전트의 코드 생성 응답 모델."""
    generated_files: List[GeneratedCode] = Field(description="생성된 코드 파일 목록")
    summary: str = Field(description="생성된 코드에 대한 요약")

# --- 2. Define Core Functional Agents (Unchanged, except for model) ---

plan_agent = LlmAgent(
    model=GEMINI_MODEL,
    name="PlanAgent",
    description="사용자 요청을 기반으로 상세한 코드 생성 계획을 수립합니다.",
    instruction="""
    당신은 숙련된 소프트웨어 아키텍트이자 프로젝트 플래너입니다.
    사용자의 요청을 받아 웹 애플리케이션 개발을 위한 상세하고 구조화된 계획을 수립해야 합니다.
    이 계획은 프론트엔드 페이지, 공통 컴포넌트, 코어 로직 등으로 분류되어야 합니다.
    각 항목에 대해 이름, 설명, 유형, 의존성을 명확히 정의하세요.
    마지막으로, 생성된 코드들을 어떻게 통합할지에 대한 간략한 단계도 포함해야 합니다.""",
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",  # Argument for npx to auto-confirm install
                    "@modelcontextprotocol/server-filesystem",
                    # IMPORTANT: This MUST be an ABSOLUTE path to a folder the
                    # npx process can access.
                    # Replace with a valid absolute path on your system.
                    # For example: "/Users/youruser/accessible_mcp_files"
                    # or use a dynamically constructed absolute path:
                    os.path.abspath(TARGET_FOLDER_PATH),
                ],
            ),
            tool_filter=['list_directory', 'read_file'],
        )
    ],
)

web_app_agent = LlmAgent(
    model=GEMINI_MODEL,
    name="WebAppAgent",
    description="프론트엔드 웹 앱 페이지 코드를 생성합니다 (React, styled-components).",
    instruction="""
    당신은 React 및 styled-components 전문가입니다.
    각 컴포넌트는 재사용 가능하고, styled-components를 사용하여 스타일링하며, 반응형 디자인을 고려해야 합니다.
    'overall_context'를 참조하여 프로젝트의 전반적인 목표를 이해하고 코드를 작성하세요.
    모든 코드는 TSX (React) 형식으로 작성되어야 합니다.
    예시: 로그인 페이지, 상품 목록 페이지 등.
    
    먼저 적합한 코드베이스의 파일들을 읽어보고 구조를 파악한뒤에 작업을 시작하세요.
    """,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",  # Argument for npx to auto-confirm install
                    "@modelcontextprotocol/server-filesystem",
                    # IMPORTANT: This MUST be an ABSOLUTE path to a folder the
                    # npx process can access.
                    # Replace with a valid absolute path on your system.
                    # For example: "/Users/youruser/accessible_mcp_files"
                    # or use a dynamically constructed absolute path:
                    os.path.abspath(TARGET_FOLDER_PATH),
                ],
            ),
        )
    ],
)

common_components_agent = LlmAgent(
    model=GEMINI_MODEL,
    name="CommonComponentsAgent",
    description="재사용 가능한 공통 UI 컴포넌트 코드를 생성합니다 (React, Tailwind CSS).",
    instruction="""
    당신은 재사용 가능한 UI 컴포넌트 개발 전문가입니다.
    제공된 'component_details'에 따라 버튼, 입력 필드, 모달 등과 같은 공통 UI 컴포넌트 코드를 생성해야 합니다.
    각 컴포넌트는 범용적이고, Tailwind CSS를 사용하여 스타일링하며, 접근성을 고려해야 합니다.
    'overall_context'를 참조하여 프로젝트의 전반적인 목표를 이해하고 코드를 작성하세요.
    모든 코드는 JSX (React) 형식으로 작성되어야 합니다.

    **출력 형식:** 반드시 'CodeGenerationResponse' Pydantic 스키마에 맞는 JSON 객체를 반환해야 합니다.
    """,
    output_schema=CodeGenerationResponse,
)

core_agent = LlmAgent(
    model=GEMINI_MODEL,
    name="CoreAgent",
    description="프론트엔드 UI 없이 메인 로직을 담고 백엔드 API를 호출하는 모듈 코드를 생성합니다.",
    instruction="""
    당신은 프론트엔드 애플리케이션의 핵심 로직 및 API 연동 전문가입니다.
    제공된 'component_details'에 따라 프론트엔드 UI와는 독립적으로 작동하는 메인 로직, 데이터 처리, 그리고 백엔드 API 호출을 위한 모듈 코드를 생성해야 합니다.
    이는 주로 JavaScript/TypeScript (React 환경 가정)로 작성되며, Fetch API 또는 Axios와 같은 라이브러리를 사용하여 백엔드와 통신하는 코드를 포함합니다.
    'overall_context'를 참조하여 프로젝트의 전반적인 목표를 이해하고 코드를 작성하세요.
    생성된 코드는 모듈화되어야 하며, 재사용 가능하도록 설계해야 합니다.
    예시: 인증 서비스 모듈, 데이터 페칭 유틸리티, 상태 관리 로직 (UI와 분리된).

    **출력 형식:** 반드시 'CodeGenerationResponse' Pydantic 스키마에 맞는 JSON 객체를 반환해야 합니다.
    """,
    output_schema=CodeGenerationResponse,
)

code_generation_pipeline_agent = SequentialAgent(
    name="CodeGenerationPipeline",
    sub_agents=[
        plan_agent,
        web_app_agent,
        common_components_agent,
        core_agent,
    ],
    description="Executes a sequence of code generation: planning, web app, components, core logic, and final report.",
)

# For ADK tools compatibility, the root agent must be named `root_agent`
root_agent = code_generation_pipeline_agent