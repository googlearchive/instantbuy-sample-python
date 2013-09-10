"""
 Copyright 2013 Google Inc. All Rights Reserved.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

 """

import json
import os
import time

import webapp2

import jwt

from google.appengine.ext.webapp import template


BAD_REQUEST = 400
CLIENT_ID = 'CLIENT_ID'
CLIENT_SECRET = 'CLIENT_SECRET'
MERCHANT_ID = 'MERCHANT_ID'
MERCHANT_SECRET = 'MERCHANT_SECRET'
MERCHANT_NAME = 'Imaginary Awesome Bike Store'
DATA_SCOPE = [
    'https://www.googleapis.com/auth/plus.login',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/paymentssandbox.make_payments']
ORIGIN = 'ORIGIN'
CURRENCY_CODE = 'USD'


def displayIndexView(request):
  """Serves the index page.

  Args:
    request: A HTTP request object.

  Returns:
    The index page.
  """
  path = os.path.join(os.path.dirname(__file__), 'index.html')
  user_email = request.cookies.get('email')

  template_values = {
      'client_id': CLIENT_ID,
      'display_login': True,
      'scopes': DATA_SCOPE
  }

  if user_email:
    template_values.update({
        'display_login': False,
        'user_email': user_email.replace('%40', '@')
    })
  return webapp2.Response(template.render(path, template_values))


def validationHandler(request):
  """Serves page to validate the jwt passed to it as a parameter.

  Args:
    request: A HTTP request object.

  Returns:
    A HttpResponse with True if jwt is valid, False otherwise.
  """
  encoded_jwt = request.params.get('jwt')
  if not encoded_jwt:
    response = webapp2.Response()
    response.set_status(BAD_REQUEST)
    response.write('JWT parameter is missing')
    return response

  decoded_jwt = jwt.decode(str(encoded_jwt), MERCHANT_SECRET)
  if decoded_jwt['iss'] == 'Google' and decoded_jwt['aud'] == MERCHANT_ID:
    return webapp2.Response('true')
  else:
    return webapp2.Response('false')


def notifyStatusHandler(request):
  """Handler to return success jwt.

  Args:
    request: HTTP request object.

  Returns:
    JWT success response.
  """
  google_transaction_id = request.POST.get('gid')
  now = int(time.time())
  data = {
      'iat': now,
      'exp': now + 3600,
      'typ': 'google/wallet/online/transactionstatus/v2',
      'aud': 'Google',
      'iss': MERCHANT_ID,
      'request': {
          'merchantName': MERCHANT_NAME,
          'googleTransactionId': google_transaction_id,
          'status': 'SUCCESS'
      }
  }
  encoded_jwt = jwt.encode(data, MERCHANT_SECRET)
  return webapp2.Response(encoded_jwt)


def logout(request):
  """Logs the user out by deleting all the session cookies.

  Args:
    request: A HTTP request object.

  Returns:
    A HttpResponse to delete all the cookies related with the session.
  """
  response = webapp2.Response()
  response.delete_cookie('email')
  response.delete_cookie('access_token')
  response.delete_cookie('gdToken')
  response.delete_cookie('currentItem')
  response.delete_cookie('cartItem')
  response.delete_cookie('fullWallet')
  response.delete_cookie('maskedWallet')
  response.delete_cookie('transactionId')
  response.delete_cookie('changedJwt')
  return response


class MWRHandler(webapp2.RequestHandler):
  def post(self):
    """Handles POST requests to serve Masked Wallet Request JWT objects.
    """
    total = float(self.request.POST.get('total'))

    google_transaction_id = self.request.POST.get('gid')
    curr_time = int(time.time())
    exp_time = curr_time + 3600
    mwr = {
        'iat': curr_time,
        'exp': exp_time,
        'typ': 'google/wallet/online/masked/v2/request',
        'aud': 'Google',
        'iss': MERCHANT_ID,
        'request': {
            'clientId': CLIENT_ID,
            'merchantName': MERCHANT_NAME,
            'origin': ORIGIN,
            'pay': {
                'estimatedTotalPrice': str(round(total, 2)),
                'currencyCode': CURRENCY_CODE
            },
            'ship': {}
        }
    }
    if google_transaction_id:
      mwr['request'].update({'googleTransactionId': google_transaction_id})
    encoded_jwt = jwt.encode(mwr, MERCHANT_SECRET)
    self.response.out.write(encoded_jwt)

  def put(self):
    """Handles POST requests to serve Masked Wallet Request JWT objects.
    """
    encoded_jwt = self.request.PUT.get('jwt')
    google_transaction_id = self.request.PUT.get('googleTransactionId')
    now = int(time.time())

    mwr = jwt.decode(str(encoded_jwt), MERCHANT_SECRET)
    mwr['iat'] = now
    mwr['exp'] = now + 3600
    mwr['request']['googleTransactionId'] = google_transaction_id
    mwr['request']['ship'] = {}
    encoded_jwt = jwt.encode(mwr, MERCHANT_SECRET)
    self.response.out.write(encoded_jwt)


class FWRHandler(webapp2.RequestHandler):
  def post(self):
    """Serves the Full Wallet Request JWT object.
    """
    cart_items = json.loads(self.request.POST.get('arrCart'))
    google_transaction_id = self.request.POST.get('gid')
    tax = float(self.request.POST.get('tax'))
    shipping = float(self.request.POST.get('shipping'))
    if not (cart_items and google_transaction_id and tax and shipping):
      response = webapp2.Response()
      response.set_status(BAD_REQUEST)
      response.write('Insufficient parametes were sent.')
      return response

    data = []
    sub_total = 0
    for item in cart_items:
      data.append({
          'description': item['name'],
          'unitPrice': str(round(item['unitPrice'], 2)),
          'quantity': item['quantity'],
          'totalPrice': str(round(item['totalPrice'], 2))
      })
      sub_total += item['totalPrice']
    data.append({
        'description': 'Shipping Detail',
        'totalPrice': str(round(shipping, 2)),
        'role': 'SHIPPING'
    })
    data.append({
        'description': 'Tax',
        'totalPrice': str(round(tax, 2)),
        'role': 'TAX'
    })
    now = int(time.time())
    fwr = {
        'iat': now,
        'exp': now + 3600,
        'typ': 'google/wallet/online/full/v2/request',
        'aud': 'Google',
        'iss': MERCHANT_ID,
        'request': {
            'merchantName': MERCHANT_NAME,
            'googleTransactionId': google_transaction_id,
            'origin': ORIGIN,
            'cart': {
                'totalPrice': str(round(
                    sub_total + tax + shipping, 2)),
                'currencyCode': CURRENCY_CODE,
                'lineItems': data
            }
        }
    }
    encoded_jwt = jwt.encode(fwr, MERCHANT_SECRET)
    self.response.out.write(encoded_jwt)


application = webapp2.WSGIApplication([
    ('/', displayIndexView),
    ('/logout', logout),
    ('/mwr', MWRHandler),
    ('/fwr', FWRHandler),
    ('/validate', validationHandler),
    ('/tsn', notifyStatusHandler)])
