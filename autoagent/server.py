from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from datetime import timedelta
from autoagent.registry import registry
from autoagent import MetaChain
from autoagent.types import Agent, Response
from autoagent.auth import (
    Token, User, UserCreate, fake_users_db,
    authenticate_user, create_access_token, get_current_active_user,
    get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
)
import importlib
import inspect

# 定义lifespan上下文管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    create_tool_endpoints()
    create_agent_endpoints()
    yield
    # 关闭时执行
    # 清理代码（如果需要）

app = FastAPI(title="MetaChain API", lifespan=lifespan)

class ToolRequest(BaseModel):
    args: Dict[str, Any]

class AgentRequest(BaseModel):
    model: str
    query: str
    context_variables: Optional[Dict[str, Any]] = {}

class Message(BaseModel):
    role: str
    content: str

class AgentResponse(BaseModel):
    result: str
    messages: List
    agent_name: str
# 为所有注册的tools创建endpoints
def create_tool_endpoints():
    for tool_name, tool_func in registry.tools.items():
        # 创建动态的POST endpoint
        async def create_tool_endpoint(request: ToolRequest, func=tool_func):
            try:
                # 检查必需参数
                sig = inspect.signature(func)
                required_params = {
                    name for name, param in sig.parameters.items()
                    if param.default == inspect.Parameter.empty
                }
                
                # 验证是否提供了所有必需参数
                if not all(param in request.args for param in required_params):
                    missing = required_params - request.args.keys()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required parameters: {missing}"
                    )
                
                result = func(**request.args)
                return {"status": "success", "result": result}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # 添加endpoint到FastAPI应用
        endpoint = create_tool_endpoint
        endpoint.__name__ = f"tool_{tool_name}"
        app.post(f"/tools/{tool_name}")(endpoint)
# 重写agent endpoints创建逻辑
def create_agent_endpoints():
    for agent_name, agent_func in registry.agents.items():
        async def create_agent_endpoint(
            request: AgentRequest, 
            func=agent_func
        ) -> AgentResponse:
            try:
                # 创建agent实例
                agent = func(model=request.model)
                
                # 创建MetaChain实例
                mc = MetaChain()
                
                # 构建messages
                messages = [
                    {"role": "user", "content": request.query}
                ]
                
                # 运行agent
                response = mc.run(
                    agent=agent,
                    messages=messages,
                    context_storage=request.context_variables,
                    debug=True
                )
                
                return AgentResponse(
                    result=response.messages[-1]['content'],
                    messages=response.messages,
                    agent_name=agent.name
                )
                
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Agent execution failed: {str(e)}"
                )
        
        endpoint = create_agent_endpoint
        endpoint.__name__ = f"agent_{agent_name}"
        app.post(f"/agents/{agent_name}/run")(endpoint)

# 获取所有可用的agents信息
@app.get("/agents")
async def list_agents():
    return {
        name: {
            "docstring": info.docstring,
            "args": info.args,
            "file_path": info.file_path
        }
        for name, info in registry.agents_info.items()
    }

# 获取特定agent的详细信息
@app.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    if agent_name not in registry.agents_info:
        raise HTTPException(
            status_code=404,
            detail=f"Agent {agent_name} not found"
        )
    
    info = registry.agents_info[agent_name]
    return {
        "name": agent_name,
        "docstring": info.docstring,
        "args": info.args,
        "file_path": info.file_path
    }

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register")
async def register(user: UserCreate):
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )

    hashed_password = get_password_hash(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "hashed_password": hashed_password,
        "disabled": False,
    }

    return {"message": "User created successfully"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"message": f"Hello {current_user.username}, this is a protected route!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)