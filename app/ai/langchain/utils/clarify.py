from typing import Dict, Tuple

from app.ai.langchain.schema.exercise import ClarifyState


def summarize_to_request_and_md(sess: Dict) -> ClarifyState:
    pass
    # memory: ConversationBufferMemory = sess["memory"]
    # llm = _get_llm(0.0)
    #
    # # 把对话历史给 summary prompt
    # history_text = "\n".join([f"{m.type}: {m.content}" for m in memory.chat_memory.messages])
    # output = llm.invoke(history_text + "\n\n" + SUMMARY_PROMPT).content
    #
    # # 解析两段
    # try:
    #     json_part = output.split("===REQUEST_JSON===")[1].split("===CONFIRM_MD===")[0].strip()
    #     md_part = output.split("===CONFIRM_MD===")[1].strip()
    # except Exception:
    #     # 速度优先：失败就返回一个可视错误
    #     state = ClarifyState(stage="clarify")
    #     state.confirm_md = "解析失败：模型输出未按协议返回。请重试：`请生成需求确认文档`"
    #     return state
    #
    # # 解析 request
    # req = ExerciseRequest.model_validate_json(json_part)
    #
    # state = ClarifyState(
    #     request=req,
    #     confirm_md=md_part,
    #     stage="confirm"
    # )
    # return state

def lesson_clarify_chat(session_id: str, user_message: str) -> Tuple[str, ClarifyState]:
    # sess = get_or_create_session(session_id,LESSON_CLARIFY_PROMPT)
    # chain: ConversationChain = sess["chain"]
    #
    # state: ClarifyState = sess["state"]
    #
    # assistant_reply = chain.predict(input=user_message)
    #
    # # 规则：如果用户明确表示要确认/生成需求文档，就进入 confirm 阶段并汇总
    # trigger_words = ["确认", "就这样", "可以了", "生成需求", "总结", "开始生成"]
    # if any(w in user_message for w in trigger_words) or assistant_reply["result"] == "end":
    #     state = summarize_to_request_and_md(sess)
    #     sess["state"] = state
    #
    # return assistant_reply, sess["state"]
    pass


def start_generate_lesson(session_id:str,user_id:str):
    pass