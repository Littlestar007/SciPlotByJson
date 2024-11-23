# sci风格曲线图绘制

读取json配置绘制曲线图

![项目示例](https://github.com/Littlestar007/SciPlotByJson/blob/main/%E6%96%B9%E8%85%94%E9%A9%B1%E5%8A%A8.svg)

## 前置库

`pip install matplotlib numpy pandas fitz`

需要安装latex，建议是MikTex

## 生成流程

采用pgf模式，先生成pdf，然后转为svg

因为有中英文混合又需要输入公式时，matplotlib内置的latex无法对一段文字分中英文用两个字体，需要用外置的latex编译器，而pgf模式下不能直接生成svg，只能转一下

对于纯英文或者不输入公式时，也可以不用pgf直接生成svg
