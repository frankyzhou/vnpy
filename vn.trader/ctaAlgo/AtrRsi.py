# encoding: UTF-8
__author__ = 'frankyzhou'

from ctaBase import *
from ctaTemplate import CtaTemplate
import numpy as np
import talib
class AtrRsi(CtaTemplate):
    """动量策略Demo"""
    className = 'ArtRsi'
    author = u'frankyzhou'

    # 策略参数
    initDays = 10       # 初始化数据所用的天数
    atrMaLength = 10    # 计算atr均线的窗口数
    atrLength = 22      # 计算atr指标的窗口数
    rsiLength = 5       # 计算RIS指标的窗口数
    rsiEntry = 16       # 计算RIS开仓信号
    trailingPercent = 0.8 #百分比移动止损

    # 策略变量
    bar = None
    barMinute = EMPTY_STRING

    bufferSize = 100  #缓存数据大小
    bufferCount = 0
    highArray = np.zeros(bufferSize)
    lowArray = np.zeros(bufferSize)
    closeArray = np.zeros(bufferSize)

    atrCount = 0
    atrArray = np.zeros(bufferSize)
    atrValue = 0
    atrMa = 0

    rsiValue = 0
    rsiBuy = 0
    rsiSell = 0
    intraTradeHigh = 0
    intraTradeLow = 0

    orderList = []
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'atrLength',
                 'atrMaLength',
                 'rsiLength',
                 'rsiEntry',
                 'trailingPercent'
                 ]

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'atrValue',
               'atrMa',
               'rsiValue',
               'rsiBuy',
               'rsiSell',
               ]

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(AtrRsi, self).__init__(ctaEngine, setting)

    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s 演示策略初始化' %self.name)

        self.rsiBuy = 50 + self.rsiEntry
        self.rsiSell = 50 - self.rsiEntry

        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)

        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'动量演示策略启动')
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'动量演示策略停止')
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        # 计算K线
        tickMinute = tick.datetime.minute
        # print tickMinute
        if tickMinute != self.barMinute:
            if self.bar:
                self.onBar(self.bar)

            bar = CtaBarData()
            bar.vtSymbol = tick.vtSymbol
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange

            bar.open = tick.lastPrice
            bar.high = tick.lastPrice
            bar.low = tick.lastPrice
            bar.close = tick.lastPrice

            bar.date = tick.date
            bar.time = tick.time
            bar.datetime = tick.datetime    # K线的时间设为第一个Tick的时间

            # 实盘中用不到的数据可以选择不算，从而加快速度
            #bar.volume = tick.volume
            #bar.openInterest = tick.openInterest

            self.bar = bar                  # 这种写法为了减少一层访问，加快速度
            self.barMinute = tickMinute     # 更新当前的分钟

        else:                               # 否则继续累加新的K线
            bar = self.bar                  # 写法同样为了加快速度

            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            bar.close = tick.lastPrice

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        print bar.datetime

        for orderID in self.orderList:
            self.cancelOrder(orderID)
        self.orderList = []

        # self.closelist.append(bar.close)
        # self.closeList.pop(0)
        # ay= np.array(self.closeList)

        self.closeArray[0:self.bufferSize-1] = self.closeArray[1:self.bufferSize]
        self.highArray[0:self.bufferSize-1] = self.highArray[1:self.bufferSize]
        self.lowArray[0:self.bufferSize-1] = self.lowArray[1:self.bufferSize]

        self.closeArray[-1] = bar.close
        self.highArray[-1] = bar.high
        self.lowArray[-1] = bar.low

        self.bufferCount += 1
        if self.bufferCount < self.bufferSize:
            return
        self.atrValue = talib.ATR(self.highArray,
                                  self.lowArray,
                                  self.closeArray,
                                  self.atrLength)[-1]
        self.atrArray[0:self.bufferSize-1] = self.atrArray[1:self.bufferSize]
        self.atrArray[-1] = self.atrValue

        self.atrCount += 1
        if self.atrCount < self.bufferSize:
            return

        self.atrMa = talib.MA(self.atrArray,
                              self.atrMaLength)[-1]
        self.rsiValue = talib.RSI(self.closeArray,
                                  self.rsiLength)[-1]
        if self.pos == 0:
            self.intraTradeHigh = bar.high
            self.intraTradeLowt = bar.low

            if self.atrValue > self.atrMa:
                if self.rsiValue > self.rsiBuy:
                    self.buy(bar.close+5, 1)
                    return
                if self.rsiValue < self.rsiSell:
                    self.short(bar.close-5, 1)
                    return

        if self.pos == 1:
            self.intraTradeHigh = max(self.intraTradeHigh, bar.high)
            self.intraTradeLow = bar.low

            longStop = self.intraTradeHigh * (1-self.trailingPercent/100)
            orderID = self.sell(longStop, 1, stop=True)
            self.orderList.append(orderID)
            return

        if self.pos == -1:
            self.intraTradeLow =min(self.intraTradeLow, bar.low)
            self.intraTradeHigh = bar.high

            shortStop = self.intraTradeLow * (1+self.trailingPercent/100)
            orderID = self.cover(shortStop, 1, stop=True)
            self.orderList.append(orderID)
            return
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass

if __name__ == '__main__':
    # 以下内容是一段回测脚本的演示，用户可以根据自己的需求修改
    # 建议使用ipython notebook或者spyder来做回测
    # 同样可以在命令模式下进行回测（一行一行输入运行）
    from ctaBacktesting import *
    # 创建回测引擎
    engine = BacktestingEngine()

    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20120101')

    # 载入历史数据到引擎中
    engine.loadHistoryData(MINUTE_DB_NAME, 'IF0000')

    # 设置产品相关参数
    engine.setSlippage(0.2)     # 股指1跳
    engine.setRate(0.3/10000)   # 万0.3
    engine.setSize(300)         # 股指合约大小

    # 在引擎中创建策略对象
    engine.initStrategy(AtrRsi, {})

    # 开始跑回测
    engine.runBacktesting()

    # 显示回测结果
    # spyder或者ipython notebook中运行时，会弹出盈亏曲线图
    # 直接在cmd中回测则只会打印一些回测数值
    engine.showBacktestingResult()