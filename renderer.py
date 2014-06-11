#!/usr/bin/env python

import os
import shutil
import subprocess

from gerblook import create_app
from gerblook.utils import *
from gerblook.models import *
from gerblook.gerber import *

color_silver = '#a0a0a0ff'
color_drills = '#111111dd'
color_black = '#000000ff'
color_white = '#ffffffff'
color_outline = '#000000'
color_copper = '#a0a0a011'

app = create_app()
with app.test_request_context():
    app.logger.info('Renderer process starting')
    while True:
        uid = app.r.brpoplpush('gerblook/renderqueue', 'gerblook/processqueue')
        app.logger.info('Processing job: %s' % uid)
        basedir = os.path.join(app.config['DATA_DIR'], uid)
        gerberdir = os.path.join(basedir, 'gerbers')
        imagedir = os.path.join(basedir, 'images')
        detail_file = os.path.join(basedir, 'details.json')
        details = json.load(open(detail_file))
        layers = details['layers'] #FIXME

        # Render background images
        app.r.set('gerblook/pcb/%s/render-progress' % uid, 10)
        app.r.set('gerblook/pcb/%s/render-activity' % uid, 'Generating background')

        background = os.path.join(imagedir, 'background.png')
        top_background = os.path.join(imagedir, 'top_background.png')
        bottom_background = os.path.join(imagedir, 'bottom_background.png')

        args = ['gerbv', '-x', 'png', '-D', details['dpi'], '-B', '1', '-o',
            background, '-b', '#ffffff']
        if 'plated_drills' in layers:
            args += ['-f', '#0000ffff', os.path.join(gerberdir, layers['plated_drills'][0])]
        if 'nonplated_drills' in layers:
            args += ['-f', '#0000ffff', os.path.join(gerberdir, layers['nonplated_drills'][0])]
        args += ['-f', '#000000ff', os.path.join(gerberdir, layers['outline'][0])]
        for layer in layers.keys():
            if layer in ('outline', 'top_soldermask'):
                continue
            try:
                args += ['-f', '#ffffffff', os.path.join(gerberdir, layers[layer][0])]
            except KeyError:
                pass
        result = call(args=args)

        args = ['convert', background, '-fill', 'red', '-floodfill', '+0,+0', 'white', 'png32:%s' % background]
        result = call(args=args)

        p1 = subprocess.Popen(['convert', background, 'text:'], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(['grep', 'white'], stdout=subprocess.PIPE, stdin=p1.stdout, stderr=open(os.devnull))
        p3 = subprocess.Popen(['head', '-1'], stdout=subprocess.PIPE, stdin=p2.stdout)
        p1.stdout.close()
        p2.stdout.close()

        output = p3.communicate()[0]
        if not output:
            app.r.set('gerblook/pcb/%s/render-progress' % uid, 0)
            app.r.set('gerblook/pcb/%s/render-activity' % uid, 'Failed to render the background')
            continue
        x, y = output.split(':')[0].split(',')

        args = ['convert', background, '-fill', details['color_background'], '-floodfill', '+%s+%s' % (x, y), 'white', 'png32:%s' % background]
        result = call(args=args)

        args = ['convert', background, '-bordercolor', 'red', '-border', '1', '-fill', 'white', '-floodfill', '+0,+0', 'red', '-shave', '1x1', 'png32:%s' % background]
        result = call(args=args)

        args = ['convert', background, '-transparent', 'white', '-transparent', 'blue']
        if app.config.get('IMAGE_SIZE', None):
            args += ['-resize', app.config['IMAGE_SIZE']]
        args += ['png32:%s' % top_background]
        result = call(args=args)

        args = ['convert', background, '-transparent', 'white', '-transparent', 'blue', '-flop']
        args += ['png32:%s' % bottom_background]
        result = call(args=args)

        app.r.set('gerblook/pcb/%s/render-progress' % uid, 20)

        # Render optional layers
        if 'plated_drills' in layers:
            app.r.set('gerblook/pcb/%s/render-activity' % uid, 'Generating plated drills layer')
            output = 'plated_drills'
            color = color_black
            outfile = os.path.join(imagedir, '%s.png' % output)

            args = ['gerbv', '-x', 'png', '-D', details['dpi'], '-B', '1', '-o', outfile, '-b', '#ffffff']
            args += ['-f', color, os.path.join(gerberdir, layers[output][0])]
            for layer in layers.keys():
                if layer == output:
                    continue
                try:
                    args += ['-f', '#ffffffff', os.path.join(gerberdir, layers[layer][0])]
                except KeyError:
                    pass
            result = call(args=args)

            args = ['convert', outfile, '-transparent', 'white']
            if app.config.get('IMAGE_SIZE', None):
                args += ['-resize', app.config['IMAGE_SIZE']]
            args += ['png32:%s' % outfile]
            result = call(args=args)

        app.r.set('gerblook/pcb/%s/render-progress' % uid, 25)

        if 'nonplated_drills' in layers:
            app.r.set('gerblook/pcb/%s/render-activity' % uid, 'Generating non-plated drills layer')
            output = 'nonplated_drills'
            color = color_black
            outfile = os.path.join(imagedir, '%s.png' % output)

            args = ['gerbv', '-x', 'png', '-D', details['dpi'], '-B', '1', '-o', outfile, '-b', '#ffffff']
            args += ['-f', color, os.path.join(gerberdir, layers[output][0])]
            for layer in layers.keys():
                if layer == output:
                    continue
                try:
                    args += ['-f', '#ffffffff', os.path.join(gerberdir, layers[layer][0])]
                except KeyError:
                    pass
            result = call(args=args)

            args = ['convert', outfile, '-transparent', 'white']
            if app.config.get('IMAGE_SIZE', None):
                args += ['-resize', app.config['IMAGE_SIZE']]
            args += ['png32:%s' % outfile]
            result = call(args=args)

        app.r.set('gerblook/pcb/%s/render-progress' % uid, 30)

        for i in range(1, 5):
            if 'inner_%s' % i in layers:
                app.r.set('gerblook/pcb/%s/render-activity' % uid, 'Generating inner layer %s' % i)
                output = 'inner_%s' % i
                color = details['color_copper']
                outfile = os.path.join(imagedir, '%s.png' % output)

                args = ['gerbv', '-x', 'png', '-D', details['dpi'], '-B', '1', '-o', outfile, '-b', '#ffffff']
                if 'plated_drills' in layers:
                    args += ['-f', '#ff0000ff', os.path.join(gerberdir, layers['plated_drills'][0])]
                if 'nonplated_drills' in layers:
                    args += ['-f', '#ff0000ff', os.path.join(gerberdir, layers['nonplated_drills'][0])]
                args += ['-f', color, os.path.join(gerberdir, layers[output][0])]
                for layer in layers.keys():
                    if layer == output:
                        continue
                    try:
                        args += ['-f', '#ffffffff', os.path.join(gerberdir, layers[layer][0])]
                    except KeyError:
                        pass
                result = call(args=args)

                args = ['convert', outfile, '-transparent', 'white', '-transparent', 'red']
                if app.config.get('IMAGE_SIZE', None):
                    args += ['-resize', app.config['IMAGE_SIZE']]
                args += ['png32:%s' % outfile]
                result = call(args=args)


        app.r.set('gerblook/pcb/%s/render-progress' % uid, 35)

        if 'top_silkscreen' in layers:
            app.r.set('gerblook/pcb/%s/render-activity' % uid, 'Generating top silkscreen layer')
            output = 'top_silkscreen'
            color = details['color_silkscreen']
            outfile = os.path.join(imagedir, '%s.png' % output)

            args = ['gerbv', '-x', 'png', '-D', details['dpi'], '-B', '1', '-o', outfile, '-b', '#ffffff']
            args += ['-f', color, os.path.join(gerberdir, layers[output][0])]
            for layer in layers.keys():
                if layer == output:
                    continue
                try:
                    args += ['-f', '#ffffffff', os.path.join(gerberdir, layers[layer][0])]
                except KeyError:
                    pass
            result = call(args=args)

            args = ['convert', outfile, '-transparent', 'white']
            if app.config.get('IMAGE_SIZE', None):
                args += ['-resize', app.config['IMAGE_SIZE']]
            args += ['png32:%s' % outfile]
            result = call(args=args)

        app.r.set('gerblook/pcb/%s/render-progress' % uid, 40)

        if 'bottom_silkscreen' in layers:
            app.r.set('gerblook/pcb/%s/render-activity' % uid, 'Generating bottom silkscreen layer')
            output = 'bottom_silkscreen'
            color = details['color_silkscreen']
            outfile = os.path.join(imagedir, '%s.png' % output)

            args = ['gerbv', '-x', 'png', '-D', details['dpi'], '-B', '1', '-o', outfile, '-b', '#ffffff']
            args += ['-f', color, os.path.join(gerberdir, layers[output][0])]
            for layer in layers.keys():
                if layer == output:
                    continue
                try:
                    args += ['-f', '#ffffffff', os.path.join(gerberdir, layers[layer][0])]
                except KeyError:
                    pass
            result = call(args=args)

            args = ['convert', outfile, '-transparent', 'white', '-flop']
            if app.config.get('IMAGE_SIZE', None):
                args += ['-resize', app.config['IMAGE_SIZE']]
            args += ['png32:%s' % outfile]
            result = call(args=args)

        # Render required layers
        app.r.set('gerblook/pcb/%s/render-progress' % uid, 45)
        app.r.set('gerblook/pcb/%s/render-activity' % uid, 'Generating top copper layer')
        output = 'top_copper'
        color = details['color_copper']
        outfile = os.path.join(imagedir, '%s.png' % output)

        args = ['gerbv', '-x', 'png', '-D', details['dpi'], '-B', '1', '-o', outfile, '-b', '#ffffff']
        if 'plated_drills' in layers:
            args += ['-f', '#ff0000ff', os.path.join(gerberdir, layers['plated_drills'][0])]
        if 'nonplated_drills' in layers:
            args += ['-f', '#ff0000ff', os.path.join(gerberdir, layers['nonplated_drills'][0])]
        args += ['-f', color, os.path.join(gerberdir, layers[output][0])]
        for layer in layers.keys():
            if layer == output:
                continue
            try:
                args += ['-f', '#ffffffff', os.path.join(gerberdir, layers[layer][0])]
            except KeyError:
                pass
        result = call(args=args)

        args = ['convert', outfile, '-transparent', 'white', '-transparent', 'red']
        if app.config.get('IMAGE_SIZE', None):
            args += ['-resize', app.config['IMAGE_SIZE']]
        args += ['png32:%s' % outfile]
        result = call(args=args)

        app.r.set('gerblook/pcb/%s/render-progress' % uid, 50)
        app.r.set('gerblook/pcb/%s/render-activity' % uid, 'Generating top soldermask layer')
        output = 'top_soldermask'
        color = '#0000ffff'
        outfile = os.path.join(imagedir, '%s.png' % output)

        args = ['gerbv', '-x', 'png', '-D', details['dpi'], '-B', '1', '-o', outfile, '-b', '#ffffff']
        args += ['-f', '#000000ff', os.path.join(gerberdir, layers['outline'][0])]
        args += ['-f', color, os.path.join(gerberdir, layers[output][0])]
        for layer in layers.keys():
            if layer == output:
                continue
            try:
                args += ['-f', '#ffffffff', os.path.join(gerberdir, layers[layer][0])]
            except KeyError:
                pass
        result = call(args=args)

        args = ['convert', outfile, '-fill', 'red', '-floodfill', '+0,+0', 'white', 'png32:%s' % outfile]
        result = call(args=args)

        args = ['convert', outfile, '-fill', details['color_background'], '-floodfill', '+%s+%s' % (x, y), 'white', 'png32:%s' % outfile]
        result = call(args=args)

        args = ['convert', outfile, '-bordercolor', 'red', '-border', '1', '-fill', 'white', '-floodfill', '+0,+0', 'red', '-shave', '1x1', 'png32:%s' % outfile]
        result = call(args=args)

        args = ['convert', outfile, '-alpha', 'set', '-channel', 'alpha', '-fill', '%sbb' % details['color_background'], '-opaque', details['color_background'], 'png32:%s' % outfile]
        result = call(args=args)

        args = ['convert', outfile, '-transparent', 'white', '-transparent', 'blue']
        if app.config.get('IMAGE_SIZE', None):
            args += ['-resize', app.config['IMAGE_SIZE']]
        args += ['png32:%s' % outfile]
        result = call(args=args)

        app.r.set('gerblook/pcb/%s/render-progress' % uid, 55)
        app.r.set('gerblook/pcb/%s/render-activity' % uid, 'Generating bottom copper layer')
        output = 'bottom_copper'
        color = details['color_copper']
        outfile = os.path.join(imagedir, '%s.png' % output)

        args = ['gerbv', '-x', 'png', '-D', details['dpi'], '-B', '1', '-o', outfile, '-b', '#ffffff']
        if 'plated_drills' in layers:
            args += ['-f', '#ff0000ff', os.path.join(gerberdir, layers['plated_drills'][0])]
        if 'nonplated_drills' in layers:
            args += ['-f', '#ff0000ff', os.path.join(gerberdir, layers['nonplated_drills'][0])]
        args += ['-f', color, os.path.join(gerberdir, layers[output][0])]
        for layer in layers.keys():
            if layer == output:
                continue
            try:
                args += ['-f', '#ffffffff', os.path.join(gerberdir, layers[layer][0])]
            except KeyError:
                pass
        result = call(args=args)

        args = ['convert', outfile, '-transparent', 'white', '-transparent', 'red', '-flop']
        if app.config.get('IMAGE_SIZE', None):
            args += ['-resize', app.config['IMAGE_SIZE']]
        args += ['png32:%s' % outfile]
        result = call(args=args)

        app.r.set('gerblook/pcb/%s/render-progress' % uid, 60)
        app.r.set('gerblook/pcb/%s/render-activity' % uid, 'Generating bottom soldermask layer')
        output = 'bottom_soldermask'
        color = '#0000ffff'
        outfile = os.path.join(imagedir, '%s.png' % output)

        args = ['gerbv', '-x', 'png', '-D', details['dpi'], '-B', '1', '-o', outfile, '-b', '#ffffff']
        args += ['-f', '#000000ff', os.path.join(gerberdir, layers['outline'][0])]
        args += ['-f', color, os.path.join(gerberdir, layers[output][0])]
        for layer in layers.keys():
            if layer == output:
                continue
            try:
                args += ['-f', '#ffffffff', os.path.join(gerberdir, layers[layer][0])]
            except KeyError:
                pass
        result = call(args=args)

        args = ['convert', outfile, '-fill', 'red', '-floodfill', '+0,+0', 'white', 'png32:%s' % outfile]
        result = call(args=args)

        args = ['convert', outfile, '-fill', details['color_background'], '-floodfill', '+%s+%s' % (x, y), 'white', 'png32:%s' % outfile]
        result = call(args=args)

        args = ['convert', outfile, '-bordercolor', 'red', '-border', '1', '-fill', 'white', '-floodfill', '+0,+0', 'red', '-shave', '1x1', 'png32:%s' % outfile]
        result = call(args=args)

        args = ['convert', outfile, '-alpha', 'set', '-channel', 'alpha', '-fill', '%sbb' % details['color_background'], '-opaque', details['color_background'], 'png32:%s' % outfile]
        result = call(args=args)

        args = ['convert', outfile, '-transparent', 'white', '-transparent', 'blue', '-flop']
        if app.config.get('IMAGE_SIZE', None):
            args += ['-resize', app.config['IMAGE_SIZE']]
        args += ['png32:%s' % outfile]
        result = call(args=args)

        app.r.set('gerblook/pcb/%s/render-progress' % uid, 65)
        app.r.set('gerblook/pcb/%s/render-activity' % uid, 'Generating composite images')
        outfile = os.path.join(imagedir, 'top.png')
        args = ['convert']
        for l in ['top_background.png', 'top_copper.png', 'top_soldermask.png']:
            args.append(os.path.join(imagedir, l))
        if 'top_silkscreen' in layers:
            args.append(os.path.join(imagedir, 'top_silkscreen.png'))
        args += ['-background', 'none', '-flatten', 'png32:%s' % outfile]
        result = call(args=args)

        outfile = os.path.join(imagedir, 'top-noalpha.png')
        args = ['convert']
        for l in ['top_background.png', 'top_copper.png', 'top_soldermask.png']:
            args.append(os.path.join(imagedir, l))
        if 'top_silkscreen' in layers:
            args.append(os.path.join(imagedir, 'top_silkscreen.png'))
        args += ['-flatten', 'png32:%s' % outfile]
        result = call(args=args)

        app.r.set('gerblook/pcb/%s/render-progress' % uid, 75)
        outfile = os.path.join(imagedir, 'bottom.png')
        args = ['convert']
        for l in ['bottom_background.png', 'bottom_copper.png', 'bottom_soldermask.png']:
            args.append(os.path.join(imagedir, l))
        if 'bottom_silkscreen' in layers:
            args.append(os.path.join(imagedir, 'bottom_silkscreen.png'))
        args += ['-background', 'none', '-flatten', 'png32:%s' % outfile]
        result = call(args=args)

        outfile = os.path.join(imagedir, 'bottom-noalpha.png')
        args = ['convert']
        for l in ['bottom_background.png', 'bottom_copper.png', 'bottom_soldermask.png']:
            args.append(os.path.join(imagedir, l))
        if 'bottom_silkscreen' in layers:
            args.append(os.path.join(imagedir, 'bottom_silkscreen.png'))
        args += ['-flatten', 'png32:%s' % outfile]
        result = call(args=args)

        app.r.set('gerblook/pcb/%s/render-progress' % uid, 85)
        # Flip bottom images back the right way
        if 'bottom_silkscreen' in layers:
            output = 'bottom_silkscreen'
            outfile = os.path.join(imagedir, '%s.png' % output)
            args = ['convert', outfile, '-fill', 'black', '-opaque', details['color_silkscreen'], '-flop']
            args += ['png32:%s' % outfile]
            result = call(args=args)

        output = 'bottom_soldermask'
        outfile = os.path.join(imagedir, '%s.png' % output)
        args = ['convert', outfile, '-flop']
        args += ['png32:%s' % outfile]
        result = call(args=args)

        output = 'bottom_copper'
        outfile = os.path.join(imagedir, '%s.png' % output)
        args = ['convert', outfile, '-flop']
        args += ['png32:%s' % outfile]
        result = call(args=args)

        app.r.set('gerblook/pcb/%s/render-progress' % uid, 95)
        if 'top_silkscreen' in layers:
            output = 'top_silkscreen'
            outfile = os.path.join(imagedir, '%s.png' % output)
            args = ['convert', outfile, '-fill', 'black', '-opaque', details['color_silkscreen']]
            args += ['png32:%s' % outfile]
            result = call(args=args)

        app.r.set('gerblook/pcb/%s/render-progress' % uid, 100)
        app.r.set('gerblook/pcb/%s/render-activity' % uid, 'Done!')
        shutil.rmtree(gerberdir)
        details['rendered'] = True
        json.dump(details, open(detail_file, 'w'))

