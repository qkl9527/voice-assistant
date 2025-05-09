import funasr

# 这里使用默认模型，也可以根据需要指定不同的模型
# asr_model = funasr.AutoModel(model="paraformer-zh")
asr_model = funasr.AutoModel(
    model="paraformer-zh",
    # model="paraformer-zh-streaming",
    vad_model="fsmn-vad",
    # punc_model="ct-punc",
    disable_update=True,
)
