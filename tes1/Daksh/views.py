from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

def Daksh(request):
    template = loader.get_template('home.html')
    return HttpResponse(template.render())

@csrf_exempt
def submitForm (request):
    if request.method == 'POST':
        test = request.POST
        print(test)
        f = open("data.txt", "a")
        f.write(str(test))
        f.close()
    template = loader.get_template('home.html')
    return HttpResponse(template.render())