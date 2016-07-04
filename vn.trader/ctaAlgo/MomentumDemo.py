# encoding: UTF-8
__author__ = 'frankyzhou'

from ctaBase import *
from ctaTemplate import CtaTemplate

class MomentumDemo(CtaTemplate):
    """动量策略Demo"""
    className = 'MomentumDemo'
    author = u'frankyzhou'

    # 策略参数
    initDays = 10   # 初始化数据所用的天数
    obverstion = 60 * 5 # 时间窗口
    overflow = 0.045 # 浮动幅度
    hand  = 35 # 最高手数

    # 策略变量
    bar = None
    barMinute = EMPTY_STRING

    prices = []             # 快速EMA均线数组
    priceNow = EMPTY_FLOAT   # 当前最新的快速EMA

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol']

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'priceNow']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(MomentumDemo, self).__init__(ctaEngine, setting)

    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'动量演示策略初始化')

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
        self.priceNow = bar.close
        self.prices.append(self.priceNow)
        ment = 0
        if len(self.prices) <= self.obverstion:
            return
        else:
            ment = (self.prices[-1] - self.prices[-self.obverstion])/self.prices[-self.obverstion]
            # print str(bar.datetime) + ":" + str(ment)
        if ment > self.overflow and self.pos < self.hand:
            self.buy(bar.close, 1)
            # print "long"
        elif ment < -self.overflow and self.pos > -self.hand:
            self.sell(bar.close, 1)
            # print "short"
        print self.pos
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