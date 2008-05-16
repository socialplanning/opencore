from PIL import Image
from Products.Archetypes.debug import log_exc
from Products.Archetypes.Field import ImageField
from Products.Archetypes.Field import _marker
from cStringIO import StringIO
from ZODB.POSException import ConflictError

# we cheat by saying we always have pil installed
HAS_PIL = True

class ScaledImageField(ImageField):
    """
    override the archetypes ImageField class by modifying the way
    scales are created

    We need certain scales to be squares. We introduce the convention
    that if the size name has the word 'square' in it, then we will
    force them to be squares.
    """
    
    def createScales(self, instance, value=_marker):
        sizes = self.getAvailableSizes(instance)
        if not HAS_PIL or not sizes:
            return
        # get data from the original size if value is None
        if value is _marker:
            img = self.getRaw(instance)
            if not img:
                return
            data = str(img.data)
        else:
            data = value

        # empty string - stop rescaling because PIL fails on an empty string
        if not data:
            return

        filename = self.getFilename(instance)

        for n, size in sizes.items():
            if size == (0,0):
                continue
            w, h = size
            id = self.getName() + "_" + n
            __traceback_info__ = (self, instance, id, w, h)
            try:
                #XXX here is the difference between the base class
                #use the convention that if the word "square" is in the
                #name of the size, then we scale to aspect ratio and crop
                if 'square' in n:
                    imgdata, format = self.cropscale(data, w, h)
                else:
                    imgdata, format = self.scale(data, w, h)
            except (ConflictError, KeyboardInterrupt):
                raise
            except:
                if not self.swallowResizeExceptions:
                    raise
                else:
                    log_exc()
                    # scaling failed, don't create a scaled version
                    continue

            mimetype = 'image/%s' % format.lower()
            image = self.content_class(id, self.getName(),
                                     imgdata,
                                     mimetype
                                     )
            # nice filename: filename_sizename.ext
            #fname = "%s_%s%s" % (filename, n, ext)
            #image.filename = fname
            image.filename = filename
            # manually use storage
            delattr(image, 'title')
            self.getStorage(instance).set(id, instance, image,
                                          mimetype=mimetype, filename=filename)

    def cropscale(self, data, width, height, default_format = 'PNG'):
        im = Image.open(StringIO(data))
        x_max, y_max = im.size

        format = im.format and im.format or default_format
        
        if y_max > x_max:  #this means that the image is taller
                           #than wide so trim the height
            trim_amt = (y_max - x_max) / 2
            box = (0, trim_amt, x_max, y_max - trim_amt)
        else: #this means that the image is wider than
            #tall, so trim the width
            trim_amt = (x_max - y_max) / 2
            box = (trim_amt, 0 ,
                   x_max - trim_amt,
                   y_max)

        im = im.crop(box)
        im = im.resize((width,height), Image.ANTIALIAS)

        thumbnail_file = StringIO()
        im.save(thumbnail_file, format, quality=self.pil_quality)
        thumbnail_file.seek(0)
        return thumbnail_file, format.lower()
