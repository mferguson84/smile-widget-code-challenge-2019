from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from products.models import Product, ProductPrice, GiftCard

# Create your views here.
@csrf_exempt
def get_price(request):
    """
    Return a price for a given product, date, and (optional) gift card code.
    """
    if request.method != 'GET':
        return JsonResponse({
            'message': 'invalid method; only GET is supported',
            'success': False
        })

    product_code = request.GET.get('productCode', '')
    date = request.GET.get('date', '')
    gift_card_code = request.GET.get('giftCardCode')

    if not product_code:
        return JsonResponse({
            'message': 'productCode is mandatory',
            'success': False
        })

    if not date:
        return JsonResponse({
            'message': 'date is mandatory',
            'success': False
        })

    parsed_date = parse_date(date)
    if not parsed_date:
        print(date)
        return JsonResponse({
            'message': 'invalid date format (YYYY-MM-DD required)',
            'success': False
        })

    try:
        product = Product.objects.get(code=product_code)
    except ObjectDoesNotExist:
        return JsonResponse({
            'message': 'could not find product with code {}'.format(product_code),
            'success': False
        })
    
    if gift_card_code:
        gift_card_query = GiftCard.objects.filter(code=gift_card_code, date_start__lte=parsed_date).order_by('-amount')
        for gift_card in gift_card_query.all():
            if not gift_card.date_end or gift_card.date_end >= parsed_date:
                break
        else:
            gift_card = None
    else:
        gift_card = None

    product_prices = product.productprice_set.filter(date_start__lte=parsed_date).order_by('price')
    for product_price in product_prices.all():
        if not product_price.date_end or product_price.date_end >= parsed_date:
            if not gift_card:
                price = product_price.formatted_price
            elif gift_card.amount < product_price.price:
                price = '${0:.2f}'.format((product_price.price - gift_card.amount) / 100)
            else:
                price = '$0.00'

            response = {
                'price': price,
                'success': True
            }
            if gift_card_code and not gift_card:
                response['message'] = 'gift card code {} not valid'.format(gift_card_code)
            elif gift_card_code and gift_card:
                response['message'] = 'gift card code {} applied'.format(gift_card_code)

            return JsonResponse(response)
    else:
        return JsonResponse({
            'message': 'could not find a price for that product',
            'success': False
        })
