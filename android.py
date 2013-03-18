#!/usr/bin/env python 
'''
guillotine.py

Copyright (C) 2012 Ken Goodridge, kenny.goodridge [at] gmail.com

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA

-----------------------

This script saves the current selection to the android res folders at
the desired sizes. 

/home/foo/drawing.svg

will export to:

/home/foo/drawing0.png
/home/foo/drawing1.png
/home/foo/drawing2.png
/home/foo/drawing3.png

etc.

'''

import os
import sys
import inkex
import simplestyle
import locale

try:
    from subprocess import Popen, PIPE
    bsubprocess = True
except:
    bsubprocess = False

def float_sort(a, b):
    '''
    This is used to sort the horizontal and vertical guide positions,
    which are floating point numbers, but which are held as text.
    '''
    return cmp(float(a), float(b))

class Android(inkex.Effect):
    """Exports selection to android resources"""
    def __init__(self):
        inkex.Effect.__init__(self)    
        self.OptionParser.add_option("--directory", action="store", 
                                        type="string", dest="directory",
                                        default=None, help="")
                                        
        self.OptionParser.add_option("--image", action="store", 
                                        type="string", dest="image", 
                                        default=None, help="")
                                        
        self.OptionParser.add_option("--size", action="store", 
                                        type="int", dest="size", 
                                        default=36, help="")
        
        self.OptionParser.add_option("--keepAspect", action="store", 
                                type="inkbool", dest="keepAspect", 
                                default=False, help="")
        
    def get_slices(self):
        slices = []
        sel_area = {}
        docHeight = self.document.getroot().get('height').replace("px", "")
        
        min_x, min_y, max_x, max_y = False, False, False, False
        for identifier in self.options.ids:
            sel_area[identifier] = {}
            for att in [ "x", "y", "width", "height" ]:
                args = [ "inkscape", "-I", identifier, "--query-"+att, self.svg_file ]
                sel_area[identifier][att] = \
                    Popen(args, stdout=PIPE, stderr=PIPE).communicate()[0]
            current_min_x = float( sel_area[identifier]["x"] )
            current_max_x = float( sel_area[identifier]["x"] ) + \
                            float( sel_area[identifier]["width"] )
            current_max_y = float(docHeight) - float( sel_area[identifier]["y"] )                            
            current_min_y = current_max_y - float( sel_area[identifier]["height"] )

            if not min_x: min_x = current_min_x
            if not min_y: min_y = current_min_y
            if not max_x: max_x = current_max_x
            if not max_y: max_y = current_max_y
            if current_min_x < min_x: min_x = current_min_x
            if current_min_y < min_y: min_y = current_min_y
            if current_max_x > max_x: max_x = current_max_x
            if current_max_y > max_y: max_y = current_max_y

        slices.append([min_x,min_y,max_x,max_y])
        return slices
        
    def get_filename_parts(self):
        
        return (self.options.directory, self.options.image)

    def check_dir_exists(self, dir):
        if not os.path.isdir(dir):
            os.makedirs(dir)

    def get_localised_string(self, str):
        return locale.format("%.f", float(str), 0)

    def export_slice(self, s, filename, ratio):
        '''
        Runs inkscape's command line interface and exports the image 
        slice from the 4 coordinates in s, and saves as the filename 
        given.
        '''
        self.check_dir_exists(os.path.dirname(filename))
        
        keepAspect = self.options.keepAspect;
        svg_file = self.args[-1]
        width = self.options.size * ratio
        height = width;
        if keepAspect:
            imgW = float(s[2])-float(s[0])
            imgH = float(s[3])-float(s[1])
            if imgH > imgW:
                width = (height/imgH) * imgW
            else:
                height = (width/imgW) * imgH
        command = "inkscape -a %s:%s:%s:%s -w %s -h %s -e \"%s\" \"%s\" " % (self.get_localised_string(s[0]), self.get_localised_string(s[1]), self.get_localised_string(s[2]), self.get_localised_string(s[3]), 
                                                                             width, height,
                                                                             filename, svg_file)
        if bsubprocess:
            p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
            return_code = p.wait()
            f = p.stdout
            err = p.stderr
        else:
            _, f, err = os.open3(command)
        f.close()
        
    def export_slices(self, slices):
        '''
        Takes the slices list and passes each one with a calculated 
        filename/directory into export_slice.
        '''
        dirname, filename = self.get_filename_parts()
        if dirname == '' or dirname == None:
            dirname = './'
        dirname = os.path.expanduser(dirname)
        dirname = os.path.expandvars(dirname)
        self.check_dir_exists(dirname)
        i = 0
        base = dirname + os.path.sep + 'res' + os.path.sep;
        for s in slices:
            f = base + os.path.sep + 'drawable-ldpi' + os.path.sep + filename + ".png"
            self.export_slice(s, f, 1.0)
            f = base + os.path.sep + 'drawable-mdpi' + os.path.sep + filename + ".png"
            self.export_slice(s, f, 4.0/3.0)
            f = base + os.path.sep + 'drawable-hdpi' + os.path.sep + filename + ".png"
            self.export_slice(s, f, 2.0)
            f = base + os.path.sep + 'drawable-xhdpi' + os.path.sep + filename + ".png"
            self.export_slice(s, f, 8.0/3.0)
            i += 1
    
    def effect(self):
        slices = self.get_slices()
        self.export_slices(slices)
    
if __name__ == "__main__":
    e = Android()
    e.affect()

