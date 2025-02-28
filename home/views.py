from typing import Any, Dict, List
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.core.cache import cache
from pathlib import Path
import shopify
import json
from shopify import GraphQL as gq
from shopify_app.decorators import shop_login_required # type: ignore
from datetime import datetime, timedelta
from .utils import schedule_call
from django.views.decorators.csrf import csrf_exempt


@shop_login_required
def index(request: 'HttpRequest') -> 'HttpResponse':
    products = shopify.Product.find(limit=3) # type: ignore
    orders = shopify.Order.find(order="created_at DESC") # type: ignore
    days = int(cache.get('days', 1))
    original_domain = shopify.ShopifyResource.url
    original_token = shopify.ShopifyResource.get_headers().get("X-Shopify-Access-Token")
    original_version = shopify.ShopifyResource.get_version() or version
    original_session = shopify.Session(original_domain, original_version, original_token)
    cache.set('original_token', original_token)
    print(original_session,original_token,original_version)
    return render(request, 'home/index.html', {'products': products, 'orders': orders,'days': days})

def clear_session(request: 'HttpRequest') -> 'HttpResponse':
    request.session.flush()
    return redirect('root_path')  # Redirect to the index view or any other view


def store_days_time(request: 'HttpRequest') -> 'HttpResponse':
    if request.method == 'POST':
        days:str = request.POST.get('days') or '1'
        cache.set('days', days)
        days_ago = (datetime.now() - timedelta(days=int(days))).strftime("%Y-%m-%d")
        # GraphQL Query with Dynamic Date
        GRAPHQL_QUERY = f"""
        {{
        orders(first:10, query: "processed_at:<{days_ago}") {{
            edges {{
            node {{
                id
                name
                customer {{
                id
                firstName
                lastName
                phone
                }}
            }}
            }}
            edges {{
            node {{
                lineItems(first:10) {{
                edges {{
                    node {{
                    id
                    title
                    quantity
                    }}
                }}
            }}
            }}
            }}
        }}
        }}
        """
        result: str = str(shopify.GraphQL().execute(GRAPHQL_QUERY)) # type: ignore
        print(result)
        result_data = json.loads(result)
        print(result_data["data"]["orders"]["edges"])
        nodes = result_data["data"]["orders"]["edges"]
        product_list: List[Dict[str, Any]] = []
        for node in nodes:
            phone = node["node"]["customer"]["phone"]
            customer_name = node["node"]["customer"]["firstName"]
            customer_id = node["node"]["customer"]["id"]
            products:List[Any] = node["node"]["lineItems"]["edges"]
            for product in products:
                product_id = product["node"]["id"]
                product_name = product["node"]["title"]
                quantity = product["node"]["quantity"]
                product_list.append({"product_id":product_id, "product_name":product_name, "quantity":quantity})
            encoded_params = json.dumps({"customer_name": customer_name, "customer_id":customer_id, "product_list": product_list})
            if phone:
                schedule_call(phone,encoded_params)
                pass
        return redirect('root_path')

@csrf_exempt
def save_feedback(request: 'HttpRequest') -> 'HttpResponse':
    print(request)
    if request.method == 'POST':
        feedback:str = request.POST.get('feedback') or ''
        customer_id:str = request.POST.get('customer_id') or ''
        product_name:str = request.POST.get('product_name') or ''
        print(f"Feedback: {feedback}, Customer ID: {customer_id}, Product Name: {product_name}")
        shop_url:str = 'vastraruchi-awaaz-ai.myshopify.com'
        token:str = cache.get('original_token')
        session = shopify.Session(shop_url,'unstable',token)
        shopify.ShopifyResource.activate_session(session)
        if feedback:
            GRAPHQL_MUTATION = """
            mutation updateCustomerNote($customerId: ID!, $note: String!) {
            customerUpdate(input: { id: $customerId, note: $note }) {
                customer {
                note
                }
                userErrors {
                field
                message
                }
            }
            }
            """
            variables = {
                "customerId": customer_id,
                "note": f"{product_name} : {feedback}"
            }
            
            result: str = str(shopify.GraphQL().execute(GRAPHQL_MUTATION, variables))
            print(result)
    shopify.ShopifyResource.clear_session()
    return redirect('root_path')

