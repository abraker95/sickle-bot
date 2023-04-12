from typing import Optional

import discord
import config
import asyncio
import requests
import random
import warnings
import validators

import PIL
from PIL import Image, ImageOps
from io import BytesIO

from main import DiscordCmdBase, DiscordBot



class CmdsImage:

    __RET_FAIL = 0
    __RET_PASS = 1

    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example =
            '\n'
            f'{config.cmd_prefix}img.zoom 2.3\n'
            f'{config.cmd_prefix}img.zoom https://imgur.com/43ssfs 2.3',
        help    = 
            'Changes image zoom. Max zoom allowed: 4.0x'
    )
    async def img_zoom(self: DiscordBot, msg: discord.Message, *args: str):
        if len(args) not in [ 1, 2 ]:
            await self.run_help_cmd(msg, 'image.zoom')
            return

        # Process and extract args
        ret, img, args = await CmdsImage.__parse_cmd(self, msg, len(args) == 1, args)
        if ret == CmdsImage.__RET_FAIL:
            return

        zoom = float(args[0])

        # Perform edit
        new_w = int(img.width*zoom)
        new_h = int(img.height*zoom)

        if (new_h > 4000) or (new_w > 4000):
            if (new_h > 1000000) or (new_w > 100000):
                warnings.warn(f'Image dimensions waaay too large ({new_w}x{new_h}), zoom: {zoom}. Old dimensions: {img.width}x{img.height}')

            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Image resize', value=f'New image will be too large')
            await msg.channel.send(None, embed=embed)
            return

        img = img.resize((new_w, new_h))

        # Save to memory
        img_out = BytesIO()
        img.save(img_out, format='png')
        img_out.seek(0)

        # Send
        await msg.channel.send(file=discord.File(img_out, 'image.png'))
        img_out.close()


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example =
            '\n'
            f'{config.cmd_prefix}img.inv\n'
            f'{config.cmd_prefix}img.inv https://imgur.com/43ssfs',
        help    = 
            'Inverts image colors'
    )
    async def img_inv(self: DiscordBot, msg: discord.Message, *args: str):
        if len(args) not in [ 0, 1 ]:
            await self.run_help_cmd(msg, 'img.inv')
            return

        # Process and extract args
        ret, img, args = await CmdsImage.__parse_cmd(self, msg, len(args) == 0, args)
        if ret == CmdsImage.__RET_FAIL:
            return

        if img.mode == 'RGBA':
            r,g,b,a = img.split()
            img = Image.merge('RGB', (r,g,b))

            img = ImageOps.invert(img)

            r,g,b = img.split()
            img = Image.merge('RGBA', (r,g,b,a))

        else:
            img = ImageOps.invert(img)

        # Save to memory
        img_out = BytesIO()
        img.save(img_out, format='png')
        img_out.seek(0)

        # Send
        await msg.channel.send(file=discord.File(img_out, 'image.png'))
        img_out.close()


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example =
            '\n'
            f'{config.cmd_prefix}img.chan r\n'
            f'{config.cmd_prefix}img.chan https://imgur.com/43ssfs r',
        help    = 
            'Extracts the red (r), green (g), blue (b), or alpha (a) channel'
    )
    async def img_chan(self: DiscordBot, msg: discord.Message, *args: str):
        if len(args) not in [ 1, 2 ]:
            await self.run_help_cmd(msg, 'img.r')
            return

        # Process and extract args
        ret, img, args = await CmdsImage.__parse_cmd(self, msg, len(args) == 0, args)
        if ret == CmdsImage.__RET_FAIL:
            return

        ch = args[0]

        if img.mode == 'RGBA':
            r,g,b,a = img.split()

            if   ch == 'r': img = r
            elif ch == 'g': img = g
            elif ch == 'b': img = b
            elif ch == 'a': img = a
            else:
                embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
                embed.add_field(name='Channel extract', value=f'Invalid channel provided')
                await msg.channel.send(None, embed=embed)
                return
        else:
            r,g,b = img.split()

            if   ch == 'r': img = r
            elif ch == 'g': img = g
            elif ch == 'b': img = b
            elif ch == 'a':
                embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
                embed.add_field(name='Channel extract', value=f'Provided image does not have an alpha channel')
                await msg.channel.send(None, embed=embed)
                return
            else:
                embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
                embed.add_field(name='Channel extract', value=f'Invalid channel provided')
                await msg.channel.send(None, embed=embed)
                return

        # Save to memory
        img_out = BytesIO()
        img.save(img_out, format='png')
        img_out.seek(0)

        # Send
        await msg.channel.send(file=discord.File(img_out, 'image.png'))
        img_out.close()


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example =
            '\n'
            f'{config.cmd_prefix}img.r\n'
            f'{config.cmd_prefix}img.r https://imgur.com/43ssfs',
        help    = 
            'Takes the red channel'
    )
    async def img_r(self: DiscordBot, msg: discord.Message, *args: str):
        await CmdsImage.img_chan['func'](self, msg, *(args[0], 'r'))


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example =
            '\n'
            f'{config.cmd_prefix}img.g\n'
            f'{config.cmd_prefix}img.g https://imgur.com/43ssfs',
        help    = 
            'Takes the green channel'
    )
    async def img_g(self: DiscordBot, msg: discord.Message, *args: str):
        await CmdsImage.img_chan['func'](self, msg, *(args[0], 'g'))


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example =
            '\n'
            f'{config.cmd_prefix}img.b\n'
            f'{config.cmd_prefix}img.b https://imgur.com/43ssfs',
        help    = 
            'Takes the blue channel'
    )
    async def img_b(self: DiscordBot, msg: discord.Message, *args: str):
        await CmdsImage.img_chan['func'](self, msg, *(args[0], 'b'))


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example =
            '\n'
            f'{config.cmd_prefix}img.a\n'
            f'{config.cmd_prefix}img.a https://imgur.com/43ssfs',
        help    = 
            'Takes the alpha channel'
    )
    async def img_a(self: DiscordBot, msg: discord.Message, *args: str):
        await CmdsImage.img_chan['func'](self, msg, *(args[0], 'a'))


    @staticmethod
    async def __parse_cmd(self: DiscordBot, msg: discord.Message, prev_msg: bool, args: str) -> "tuple[int, Optional[Image.Image], tuple[str]]":
        img_url = None
        arg_start = 0

        if prev_msg or isinstance(prev_msg, type(None)):
            img_url = await CmdsImage.__extract_from_prev_msg(self, msg)
            if prev_msg and isinstance(img_url, type(None)):
                return ( CmdsImage.__RET_FAIL, None, [] )

        if not prev_msg or isinstance(img_url, type(None)):
            if len(args) == 0:
                return ( CmdsImage.__RET_FAIL, None, [] )

            # Look at args for image link
            img_url = args[0]
            arg_start = 1

        # Extract image
        img = await CmdsImage.__extract_from_url(self, msg, img_url)
        if isinstance(img, type(None)):
            return ( CmdsImage.__RET_FAIL, None, [] )

        return ( CmdsImage.__RET_PASS, img, args[arg_start:] )


    @staticmethod
    async def __extract_from_prev_msg(self: DiscordBot, msg: discord.Message) -> str:
        data = self.get_prev_msg(msg.channel.id)
        if isinstance(data, type(None)):
            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Image fetch', value=f'Image not provided')
            await msg.channel.send(None, embed=embed)
            return None

        data = data.attachments
        if len(data) != 1:
            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Image fetch', value=f'Unable to resolve which image from prev message')
            await msg.channel.send(None, embed=embed)
            return None

        data = data[0]
        if 'image/' not in data.content_type:
            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Image fetch', value=f'Unable to resolve image from prev message')
            await msg.channel.send(None, embed=embed)
            return None

        return data.proxy_url


    @staticmethod
    async def __extract_from_url(self: DiscordBot, msg: discord.Message, url: str) -> Image:
        if not validators.url(url):
            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Image fetch', value=f'Invalid image url')
            await msg.channel.send(None, embed=embed)
            return None

        reply = requests.get(url)
        if reply.status_code != 200:
            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Image fetch', value=f'Unable to fetch image')
            await msg.channel.send(None, embed=embed)
            return None

        try: img = Image.open(BytesIO(reply.content))
        except PIL.UnidentifiedImageError:
            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Image fetch', value=f'Not an image')
            await msg.channel.send(None, embed=embed)
            return None

        return img
        
