from django.http import JsonResponse
from airam_app.graph import build_graph


def graph_json(request):
    return JsonResponse(build_graph())
