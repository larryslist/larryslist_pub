import base64
from datetime import datetime, timedelta
import hashlib
import hmac
import urllib
from larryslist.lib.baseviews import GenericErrorMessage, GenericSuccessMessage
from larryslist.website.apps.cart import PLAN_SELECTED_TOKEN
import logging
from larryslist.website.apps.models import CreatePurchaseCreditProc, CheckPurchaseCreditProc, RefreshUserProfileProc, SpendCreditProc, \
                                        PaymentTransaction, UserCredits
from pyramid.renderers import render_to_response

log = logging.getLogger(__name__)

REQUEST_ORDER = ["paymentAmount","currencyCode","shipBeforeDate","merchantReference"
                    ,"skinCode","merchantAccount","sessionValidity","shopperEmail"
                    ,"shopperReference","recurringContract","allowedMethods","blockedMethods"
                    ,"shopperStatement","merchantReturnData","billingAddressType","offset"]
RESULT_ORDER = ["authResult", "pspReference", "merchantReference", "skinCode", "merchantReturnData"]


def get_signature(secret, params, sign_order = None):
    sign_order = sign_order or REQUEST_ORDER
    sign_base = ''.join([unicode(params.get(k, "")) for k in sign_order])
    hm = hmac.new(secret, sign_base, hashlib.sha1)
    return base64.encodestring(hm.digest()).strip()

def verify_signature(secret, params):
    merchantSig = params.get('merchantSig')
    if get_signature(secret, params, sign_order = RESULT_ORDER) == merchantSig:
        return params['merchantReturnData']
    else:
        return None

def get_request_parameters(standard_params, params):
    sign_base = standard_params.copy()
    sign_base["shipBeforeDate"] = (datetime.now() + timedelta(1)).strftime("%Y-%m-%d")
    sign_base["sessionValidity"] = (datetime.now() + timedelta(0, 1800)).strftime("%Y-%m-%dT%H:%M:%SZ")
    sign_base.update(params)
    return sign_base




def checkout_preview(context, request):
    """
    Checkout for Worldpay based on checkout_handler function
    """
    settings = request.globals.website
    
    installationId=settings.worldpayId
    url= settings.worldpayUrl

    planToken = request.session.get(PLAN_SELECTED_TOKEN)
    plan = context.config.getPaymentOption(planToken)
    payment = CreatePurchaseCreditProc(request, {'userToken':context.user.token, 'paymentOptionToken': plan.token})
    standard_params = {}
    
    formatCurrency = lambda v: v[:-2]+"."+v[-2:]


    redirect_params = {
        "amount": formatCurrency(unicode(payment.amount))
        ,"currency": "USD"
        ,"lang":'en_US'
        ,"cartId" : payment.paymentRef
        ,"M_shopperReference" : payment.shopperRef
        ,"M_planToken" : request.session.get(PLAN_SELECTED_TOKEN)
        ,"email" : payment.shopperEmail
        ,"instId" : installationId
        ,"resURL":request.fwd_url("website_checkout_result")
        ,"testMode":settings.worldpayTestMode
        ,"noLanguageMenu": "true"
        ,"hideCurrency": "true"
    }

    params = get_request_parameters(standard_params, redirect_params)
    urlparams = '&'.join(['%s=%s' % (k, urllib.quote(v)) for k,v in params.iteritems()])

    if request.session.get(PLAN_SELECTED_TOKEN):
        del request.session[PLAN_SELECTED_TOKEN]
    request.fwd_raw("%s?%s" % (url, urlparams))



def payment_result(context, request):
    user = request.root.user
    if user.isAnon():
        request.fwd("website_index")
    RefreshUserProfileProc(request, {'token':user.token})
    request.fwd("website_index_member", _query= [('payment', 'done')])

def payment_result_handler(context, request):
    log.info( 'PAYMENT RETURN from External: %s' , dict(request.params) )
    result = CheckPurchaseCreditProc( request, dict(request.params) )
    return {}