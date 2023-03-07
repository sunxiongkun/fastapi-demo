#!/usr/bin/env
# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException
from . import service

# 属于该模块的路由
router = APIRouter(
    # 这里配置的 tags、dependencies、responses 对这个模块的内的所有路径操作都生效
    # 路径前缀，该模块下所有路径操作的前缀
    prefix="/ai_picture",
    # 标签
    tags=["ai_picture"],
    # 依赖项
    dependencies=[],
    # 响应
    responses={404: {"description": "ai_picture not found"}}
)


@router.post(path="/q")
async def get_ai_picture(question: str = ''):
    ai_picture = service.get_ai_picture(question)
    if ai_picture is None:
        raise HTTPException(status_code=404, detail="ai_picture not found")
    return {
        "code": 200,
        "message": 'success',
        "data": f'{ai_picture}',
        "success": True,
    }
