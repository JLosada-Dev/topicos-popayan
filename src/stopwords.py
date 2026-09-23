"""Stopwords para el texto de c-TF-IDF.

Lista propia en vez de una dependencia externa (nltk, spacy), para que el pipeline
corra sin descargas y el notebook sea reproducible también en Colab.

Solo se usan en `texto_limpio`. El texto de los embeddings conserva las stopwords,
según la decisión registrada en CLAUDE.md.
"""

# Artículos, preposiciones, pronombres, conjunciones y verbos soporte del español
STOPWORDS_ES = frozenset(
    """
    a al algo alguna algunas alguno algunos ante antes aquel aquella aquellas aquello
    aquellos aqui asi aun aunque bajo bien cada casi como con contra cual cuales cuando
    cuanto cuanta cuantas cuantos de del desde donde dos e el ella ellas ello ellos en
    entre era eran eras eres es esa esas ese eso esos esta estaba estaban estamos estan
    estar estas este esto estos estoy fue fueron fui fuimos ha habia habian han has hasta
    hay he hemos hizo incluso la las le les lo los mas me mi mia mias mio mios mis mucha
    muchas mucho muchos muy nos nosotras nosotros nuestra
    nuestras nuestro nuestros o os otra otras otro otros para pero poco pocos por porque
    pues que quien quienes se sea sean segun ser si siempre sido sobre sois somos son
    soy su sus suya suyas suyo suyos tambien tampoco tan tanta tantas tanto tantos te
    tenemos tener tengo ti tiene tienen toda todas todo todos tu tus tuya tuyo un una
    unas uno unos usted ustedes va vamos van vos vosotras vosotros voy vuestra vuestro y
    ya yo
    """.split()
)

# Términos del dominio presentes en casi toda reseña, que no separan tópicos.
# Deliberadamente corta: NO entran aquí las palabras que nombran una dimensión
# (comida, servicio, ambiente, precio, lugar, sitio, espera), porque son justamente
# las que hacen interpretable cada tópico en el c-TF-IDF.
STOPWORDS_PROPIAS = frozenset(
    """
    popayan popayán cauca colombia restaurante restaurantes
    """.split()
)

# Marcas de negación. NO son stopwords: «No lo recomiendo» y «Lo recomiendo» son
# fragmentos opuestos, y sin ellas el c-TF-IDF etiqueta un tópico con su contrario
# exacto. Se declaran aparte porque varias tienen dos letras y hay que eximirlas del
# largo mínimo de `texto_para_ctfidf`.
NEGACIONES = frozenset(
    """
    no ni sin nada nunca jamas jamás ningun ningún ninguna ninguno tampoco
    """.split()
)

STOPWORDS = frozenset((STOPWORDS_ES | STOPWORDS_PROPIAS) - NEGACIONES)
