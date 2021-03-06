from datetime import timedelta, datetime

from jsonclient import ListField, DictField, Mapping, TextField, IntegerField, BooleanField
from pyramid.decorator import reify
import simplejson

from larryslist.lib import i18n
from larryslist.models import ClientTokenProc
from larryslist.models.config import ConfigModel
from larryslist.models.collector import CollectorModel as FullCollectorModel
from larryslist.models.collector import SimpleCollectorModel as CollectorModel


class PaymentOptionModel(Mapping):
    PERIOD = 'year'
    credit = IntegerField()
    price = IntegerField()
    token = TextField()
    #preferred = BooleanField()
    label = TextField()

    def getValue(self, request): return self.token
    def getKey(self, request): return self.token

    @property
    def preferred(self):
        return self.credit == 25

    @property
    def is_custom_qty(self):
        return self.credit == 1

    def getRecommendedCredits(self, cart):
        noProfiles = len(cart.getItems())
        return noProfiles if noProfiles and self.is_custom_qty else self.credit

    def getRecommendedPrice(self, request):
        noProfiles = len(request.root.cart.getItems())
        if noProfiles and self.is_custom_qty:
            return i18n.format_currency(self.price * noProfiles / 100.0, 'USD', request)
        else:
            return i18n.format_currency(self.price / 100, 'USD', request)


    def getCredits(self):
        return self.credit
    def getFormattedPrice(self, request):
        return i18n.format_currency(self.price / 100, 'USD', request)



    def getSavedAmount(self, request):
        return i18n.format_currency(10 * self.credit - self.price / 100, 'USD', request)
    def getPerCreditAmount(self, request):
        return i18n.format_currency(int(self.price / 100 / self.credit), 'USD', request)

class WebsiteConfigModel(ConfigModel):
    LABEL = ['Per Profile', 'Basic', 'Premium']
    _PaymentOption = ListField(DictField(PaymentOptionModel), name='PaymentOption')
    @reify
    def PaymentOption(self):
        po = self._PaymentOption[:3]
        for i, p in enumerate(po):
            p.label = self.LABEL[i]
        return po
    @reify
    def optionMap(self):
        return {o.token: o for o in self.PaymentOption}
    def getPaymentOptions(self):
        options = self.PaymentOption
        options[1].preferred = True
        return options
    def getPaymentOption(self, token):
        return self.optionMap[token]



#  ============================= CART SECTION =============================






class WebsiteCart(object):
    Collectors = []

    def setContent(self, json):
        self.Collectors = json.get('Collectors', [])
    def getContent(self, stringify = False):
        cart = self.Collectors
        return simplejson.dumps({'Collectors':cart})

    def getItems(self):
        return self.Collectors or []
    def getCollectors(self):
        return map(CollectorModel.wrap, self.Collectors)
    def canSpend(self, user):
        return user.getCredits() >= len(self.getItems()) > 0
    def empty(self):
        self.Collectors = []


class PaymentStatusModel(Mapping):
    success = BooleanField()
    message = TextField()


class PaymentModel(Mapping):
    paymentRef = TextField()
    amount = IntegerField()
    currency = TextField()
    shopperRef = TextField()
    shopperEmail = TextField()


#  ============================= USER SECTION =============================


SESSION_KEY = 'WEBSITE_USER'

def LoggingInProc(path, db_messages = []):
    sproc = ClientTokenProc(path, root_key='User', result_cls=UserModel)
    def f(request, data):
        result = sproc(request, data)
        request.session[SESSION_KEY] = request.root.user = result
        return result
    return f

def getUserFromSession(request):
    return request.session.get(SESSION_KEY, UserModel(token=None, name = 'Anon'))

def logoutAdmin(request):
    if SESSION_KEY in request.session:
        del request.session[SESSION_KEY]
    request.fwd("website_index")

class UserModel(Mapping):
    token = TextField()
    name = TextField()
    email = TextField()
    credit = IntegerField(default = 0)
    cardNumber = TextField()
    Collector = ListField(DictField(FullCollectorModel))

    def isAnon(self):
        return self.token is None
    def getCredits(self):
        return self.credit
    def toJSON(self, stringify = True):
        json = self.unwrap(sparse = True).copy()
        json['Collector'] = [{'id': c['id'], 'firstName':c['firstName'], 'lastName':c['lastName']} for c in json.pop("Collector", []) if c.get('id')]
        return simplejson.dumps(json)
    def hasSavedDetails(self):
        return bool(self.cardNumber)
    def discardSavedDetails(self):
        self.cardNumber = None
        return True
    def getCreditWithPlan(self, plan):
        return self.credit + plan.credit

    @reify
    def collectorMap(self):
        return {c.id: c for c in self.Collector}
    def getCollector(self, id):
        return self.collectorMap.get(int(id))
    def hasCollector(self, collector):
        return isinstance(self.collectorMap.get(collector.id), CollectorModel)

    def getCreditValidity(self, request):
        return i18n.format_date(datetime.now() + timedelta(356), request)

SignupProc = LoggingInProc("/user/signup")
LoginProc = LoggingInProc("/user/login")
PasswordRequestProc = ClientTokenProc("/user/forgotpwd")
ResendRequestProc = ClientTokenProc("/user/resendForgotPwd")
UpdatePasswordProc = ClientTokenProc("/user/updatePwd")
PasswordTokenVerifyProc = ClientTokenProc("/user/token", root_key = "User", result_cls = UserModel)
CheckEmailExistsProc = ClientTokenProc('/user/emailavailable')
RefreshUserProfileProc = LoggingInProc("/user/profile")


CreatePurchaseCreditProc = ClientTokenProc("/web/credit/buy", result_cls=PaymentModel, root_key="Payment")
CheckPurchaseCreditProc = ClientTokenProc("/web/credit/paymentResult", result_cls=PaymentStatusModel, root_key="PaymentStatus")
SpendCreditProc = LoggingInProc("/web/credit/spend")


GetCollectorProc = ClientTokenProc("/web/user/getcollector", result_cls=FullCollectorModel, root_key="Collector")

