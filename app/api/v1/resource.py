import os
import shutil
import requests

from fastapi import APIRouter, Depends, Path, UploadFile, File
from typing import List

from starlette.responses import JSONResponse

from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

file_end = ["txt","doc","pdf","url","docx","ppt","pptx","md"]
res_dir='./app/resource/'


@router.post("/upload")
async def upload_resource(file: UploadFile = File(description="文件上传路径"),
                        current_user: User = Depends(get_current_user),
                        file_path:str = Path(description="自定义上传路径")):
    """上传文件到服务器"""
    #TODO:未来修改成上传到专用OSS,可以加入Redis进行优化
    if not file.filename in file_end:
        return JSONResponse(status_code=400,
                            content={"message": f"文件格式错误，仅支持{file_end}格式"
                                    })
    save_dir=res_dir+file.filename if not file_path else res_dir+file_path
    os.makedirs(save_dir, exist_ok=True)
    with open(os.path.join(save_dir, file.filename), 'wb') as f:
        shutil.copyfileobj(file.file, f)

    return {
        "message": f"上传文件成功，上传路径{save_dir}",
        "contentType": file.content_type,
        "file_size": os.path.getsize(save_dir)
    }


async def upload_nordb(
        file_path:str = Path(description="在服务器上的文件路径"),

):
    #TODO:后续加入Redis进行缓存


@router.get("/list")
async def get_resource_list(current_user: User = Depends(get_current_user)):
    """获取资源库内容（分页/分类）"""
    return {"message": "获取资源列表功能待实现"}


@router.delete("/{id}")
async def delete_resource(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """删除资源"""
    return {"message": f"删除资源功能待实现，资源ID: {id}"}


@router.put("/{id}")
async def update_resource(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """修改资源信息（名称/标签）"""
    return {"message": f"修改资源信息功能待实现，资源ID: {id}"}


# 资源标签
@router.get("/tags")
async def get_resource_tags(current_user: User = Depends(get_current_user)):
    """获取全部标签"""
    return {"message": "获取资源标签列表功能待实现"}


@router.post("/tags")
async def create_resource_tag(current_user: User = Depends(get_current_user)):
    """新增标签"""
    return {"message": "新增资源标签功能待实现"}


@router.delete("/tags/{tag}")
async def delete_resource_tag(tag: str = Path(...), current_user: User = Depends(get_current_user)):
    """删除标签"""
    return {"message": f"删除资源标签功能待实现，标签: {tag}"}

def upload_nordb_resp(
        file_path:str = Path(description="文件在服务器上的路径"),
        knowledge_type: str=Path(description="知识库类型"),

)->bool:

    url = "https://open.bigmodel.cn/api/llm-application/open/document/upload_document/1999002185098272768"

    files = {"files": ("example-file", open("example-file", "rb"))}
    payload = {
        "knowledge_type": "123",
        "custom_separator": "<string>",
        "sentence_size": "123",
        "parse_image": "true",
        "callback_url": "<string>",
        "callback_header": "{}",
        "word_num_limit": "<string>",
        "req_id": "<string>"
    }
    headers = {"Authorization": "Bearer REMOVED_ZHIPU_API_KEY"}

    response = requests.post(url, data=payload, files=files, headers=headers)

    print(response.text)