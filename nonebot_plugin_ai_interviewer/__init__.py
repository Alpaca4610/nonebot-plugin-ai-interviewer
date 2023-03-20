import nonebot

from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.adapters.onebot.v11 import MessageEvent
from .config import Config, ConfigError
from .interviewer import Interviewer

plugin_config = Config.parse_obj(nonebot.get_driver().config.dict())

if not plugin_config.openai_api_key:
    api_key = ""
else:
    api_key = plugin_config.openai_api_key
model_id = plugin_config.openai_model_name
session = {}

chat_request = on_command("interview", block=True, priority=1)


@chat_request.handle()
async def _(event: MessageEvent, msg: Message = CommandArg()):
    if api_key == "":
        await chat_request.finish(MessageSegment.text("请先配置openai_api_key"), at_sender=True)

    content = msg.extract_plain_text()

    if content == "" or content is None:
        await chat_request.finish(MessageSegment.text("内容不能为空！"), at_sender=True)

    if event.get_session_id() not in session:
        await chat_request.send(MessageSegment.text("没有面试数据，即将开始新一轮的面试"))
        company = content.split("：")[1].split("，")[0]
        job = content.split("：")[2]
        try:
            session[event.get_session_id()] = Interviewer(api_key=api_key, model_id=model_id, company=company, job=job)
            res = await session[event.get_session_id()].init_interview()
        except Exception as error:
            await chat_request.finish(str(error), at_sender=True)
        await chat_request.finish(MessageSegment.text(res), at_sender=True)

    else:
        await chat_request.send(MessageSegment.text("面试官思考中"))
        try:
            res = await session[event.get_session_id()].get_ans(content)
        except Exception as error:
            await chat_request.finish(str(error), at_sender=True)
        await chat_request.finish(MessageSegment.text(res), at_sender=True)




clear_request = on_command("stop", block=True, priority=1)


@clear_request.handle()
async def _(event: MessageEvent):
    try:
        del session[event.get_session_id()]
    except Exception as error:
        await chat_request.finish(str(error), at_sender=True)
    await clear_request.finish(MessageSegment.text("面试停止！程序将清除你的面试记录"), at_sender=True)
