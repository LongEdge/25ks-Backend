import os
from typing import Dict, Tuple

from langchain_classic.chains.conversation.base import ConversationChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatZhipuAI
from app.ai.langchain.prompts.CLARIFY import  SUMMARY_PROMPT, CLARIFY_PROMPT
from app.ai.langchain.schema.exercise import ClarifyState, ExerciseRequest
from app.core.config import settings

# 速度优先：进程内 session 存储
_SESSIONS: Dict[str, Dict] = {}

TES="""
根据您的要求，以下是高二语文《赤壁赋》的作业生成需求文档：\n\n一、作业主题：《赤壁赋》单选题\n\n二、作业内容：\n\n1. 《赤壁赋》的作者苏轼是哪个朝代的文学家？\nA. 宋朝\nB. 唐朝\nC. 元朝\nD. 明朝\n\n2. 《赤壁赋》中，苏轼描绘了哪种景象？\nA. 江山如画\nB. 大漠孤烟直\nC. 春水碧于天\nD. 高山仰止\n\n3. 以下哪句话出自《赤壁赋》？\nA. 人生自古谁无死，留取丹心照汗青\nB. 两岸猿声啼不住，轻舟已过万重山\nC. 月落乌啼霜满天，江枫渔火对愁眠\nD. 大江东去，浪淘尽，千古风流人物\n\n4. 《赤壁赋》中，苏轼提到了哪个历史事件？\nA. 官渡之战\nB. 赤壁之战\nC. 淝水之战\nD. 长平之战\n\n5. 以下哪个词在《赤壁赋》中用来形容周瑜？\nA. 雄姿英发\nB. 风华绝代\nC. 睿智聪慧\nD. 威风凛凛\n\n6. 《赤壁赋》中，苏轼对曹操的评价是什么？\nA. 英雄豪杰\nB. 智勇双全\nC. 贪婪无厌\nD. 刚愎自用\n\n7. 以下哪个诗句出自《赤壁赋》？\nA. 白日依山尽，黄河入海流\nB. 床前明月光，疑是地上霜\nC. 野旷天低树，江清月近人\nD. 对海而唱，临江仙·赤壁怀古\n\n8. 《赤壁赋》中，苏轼提到了哪种动物？\nA. 鹰\nB. 马踏飞燕\nC. 鹤\nD. 鲲鹏\n\n9. 《赤壁赋》中，苏轼对人生的看法是什么？\nA. 人生得意须尽欢，莫使金樽空对月\nB. 人生自古谁无死，留取丹心照汗青\nC. 人生如梦，一尊还酹江月\nD. 人生若只如初见，何事秋风悲画扇\n\n10. 《赤壁赋》中，苏轼对友情的描述是什么？\nA. 同是天涯沦落人，相逢何必曾相识\nB. 海内存知己，天涯若比邻\nC. 莫愁前路无知己，天下谁人不识君\nD. 世人谓我恋长安，其实只恋长安某\n\n三、作业要求：\n1. 请同学们认真阅读《赤壁赋》，理解课文内容。\n2. 根据题目要求，选择正确答案。\n3. 作业完成后，请同学们互相交流，共同提高。\n\n四、作业提交时间：请根据老师的要求按时提交。\n\n以上为《赤壁赋》单选题作业需求文档，请您查阅。如有需要修改或补充，请随时告知。
"""

def _get_llm(temp: float = 0.2):
    # ChatZhipuAI 会从环境变量 ZHIPUAI_API_KEY 读取
    return ChatZhipuAI(model="glm-4", temperature=temp,zhipuai_api_key=settings.AI_API_KEY)


def get_or_create_session(session_id: str,prompt:str) -> Dict:
    if session_id not in _SESSIONS:
        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="history"
        )
        chain = ConversationChain(
            llm=_get_llm(0.2),
            memory=memory,
            prompt=prompt,  # ✅ 正确用法
        )
        _SESSIONS[session_id] = {
            "chain": chain,
            "memory": memory,
            "state": ClarifyState(),
        }
    return _SESSIONS[session_id]


#===========================================================#===========================================================

def clarify_chat(session_id: str, user_message: str) -> Tuple[str, ClarifyState]:
    sess = get_or_create_session(session_id,CLARIFY_PROMPT)
    chain: ConversationChain = sess["chain"]
    state: ClarifyState = sess["state"]

    assistant_reply = chain.predict(input=user_message)


    # 规则：如果用户明确表示要确认/生成需求文档，就进入 confirm 阶段并汇总
    trigger_words = ["确认", "就这样", "可以了", "生成需求", "总结", "开始生成"]
    if any(w in user_message for w in trigger_words):
        state = summarize_to_request_and_md(sess)
        sess["state"] = state

    return assistant_reply, sess["state"]


def summarize_to_request_and_md(sess: Dict) -> ClarifyState:
    memory: ConversationBufferMemory = sess["memory"]
    llm = _get_llm(0.0)

    # 把对话历史给 summary prompt
    history_text = "\n".join([f"{m.type}: {m.content}" for m in memory.chat_memory.messages])
    output = llm.invoke(history_text + "\n\n" + SUMMARY_PROMPT).content

    # 解析两段
    try:
        json_part = output.split("===REQUEST_JSON===")[1].split("===CONFIRM_MD===")[0].strip()
        md_part = output.split("===CONFIRM_MD===")[1].strip()
    except Exception:
        # 速度优先：失败就返回一个可视错误
        state = ClarifyState(stage="clarify")
        state.confirm_md = "解析失败：模型输出未按协议返回。请重试：`请生成需求确认文档`"
        return state

    # 解析 request
    req = ExerciseRequest.model_validate_json(json_part)

    state = ClarifyState(
        request=req,
        confirm_md=md_part,
        stage="confirm"
    )
    return state


def apply_confirm_md(session_id: str, confirm_md_final: str) -> ClarifyState:
    sess = get_or_create_session(session_id,CLARIFY_PROMPT)
    state: ClarifyState = sess["state"]
    state.confirm_md_final = confirm_md_final
    state.stage = "generate"
    sess["state"] = state
    return state


def get_state(session_id: str) -> ClarifyState:
    return get_or_create_session(session_id,CLARIFY_PROMPT)["state"]

#===========================================================#===========================================================



