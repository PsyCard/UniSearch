import json

# Load current data
with open('data.json', 'r', encoding='utf-8') as f:
    universities = json.load(f)

career_prices = {
    'Derecho': {'Publica':500000,'Privada':2500000},
    'Administración': {'Publica':450000,'Privada':2000000},
    'Ingeniería Civil': {'Publica':600000,'Privada':2800000},
    'Medicina': {'Publica':800000,'Privada':4500000},
    'Ingeniería de Sistemas': {'Publica':650000,'Privada':3000000},
    'Comunicación Social': {'Publica':400000,'Privada':2200000},
    'Psicología': {'Publica':550000,'Privada':2400000},
    'Ingeniería Industrial': {'Publica':700000,'Privada':3200000},
    'Diseño': {'Publica':480000,'Privada':2300000},
    'Economía': {'Publica':520000,'Privada':2600000},
    'Contaduría': {'Publica':490000,'Privada':2100000},
    'Negocios Internacionales': {'Publica':530000,'Privada':2700000},
    'Comunicación': {'Publica':420000,'Privada':2000000},
    'Educación Física': {'Publica':380000,'Privada':1800000},
    'Pedagogía Infantil': {'Publica':350000,'Privada':1600000},
    'Lenguas': {'Publica':400000,'Privada':1900000},
    'Ingeniería Química': {'Publica':720000,'Privada':3100000},
    'Biotecnología': {'Publica':700000,'Privada':3000000},
    'Farmacia': {'Publica':650000,'Privada':2900000},
    'Trabajo Social': {'Publica':420000,'Privada':2000000},
    'Artes Visuales': {'Publica':460000,'Privada':2200000},
    'Diseño Gráfico': {'Publica':480000,'Privada':2400000},
    'Música': {'Publica':500000,'Privada':2300000},
    'Tecnología Electrónica': {'Publica':680000,'Privada':2900000},
    'Mecánica Industrial': {'Publica':700000,'Privada':3000000},
    'Automatización': {'Publica':690000,'Privada':2950000},
    'Emprendimiento': {'Publica':550000,'Privada':2500000},
    'Desarrollo Web': {'Publica':600000,'Privada':2800000},
    'Data Science': {'Publica':700000,'Privada':3200000},
    'Tecnología Ambiental': {'Publica':550000,'Privada':2400000},
    'Ingeniería Electrónica': {'Publica':720000,'Privada':3100000},
    'Ciencias Sociales': {'Publica':450000,'Privada':2000000},
    'Salud Pública': {'Publica':650000,'Privada':2800000},
    'Historia': {'Publica':380000,'Privada':1700000},
    'Ingeniería': {'Publica':700000,'Privada':3200000},
    'Ciencias Básicas': {'Publica':500000,'Privada':2200000},
    'Náutica': {'Publica':800000,'Privada':3500000},
    'Logística Marítima': {'Publica':700000,'Privada':3200000},
    'Ingeniería Naval': {'Publica':800000,'Privada':3600000},
    'Técnico en Sistemas': {'Publica':450000,'Privada':1800000},
    'Administración de Empresas': {'Publica':480000,'Privada':2000000},
    'Hotelería': {'Publica':400000,'Privada':1700000},
    'Marketing': {'Publica':500000,'Privada':2200000},
    'Artes': {'Publica':450000,'Privada':2100000},
}

# Check duplicates
ids = [u['id'] for u in universities]
names = [u['name'] for u in universities]
print('Total universidades:', len(universities))
print('IDs duplicados:', len(ids)-len(set(ids)))
print('Nombres duplicados:', len(names)-len(set(names)))

# transform
for uni in universities:
    newcars=[]
    for c in uni.get('careers',[]):
        if isinstance(c,str):
            price = career_prices.get(c,{}).get(uni['type'], None)
            newcars.append({'name':c,'price':price})
        else:
            newcars.append(c)
    uni['careers']=newcars
    uni.pop('tuition',None)

with open('data.json','w',encoding='utf-8') as f:
    json.dump(universities,f,ensure_ascii=False,indent=2)

print('Transform complete. Sample:', universities[0]['careers'][:3])
