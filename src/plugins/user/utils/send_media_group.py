import os
import re
from datetime import datetime
from typing import Union, List

from pyrogram import raw, Client
from pyrogram import types
from pyrogram import utils
from pyrogram.file_id import FileType


async def send_media_group(
    client: Client,
    chat_id: Union[int, str],
    media: List[Union[
        "types.InputMediaPhoto",
        "types.InputMediaVideo",
        "types.InputMediaAudio",
        "types.InputMediaDocument"
    ]],
    disable_notification: bool = None,
    reply_to_message_id: int = None,
    schedule_date: datetime = None,
    protect_content: bool = None,
) -> List["types.Message"]:
    multi_media = []

    for i in media:
        if isinstance(i, types.InputMediaPhoto):
            if isinstance(i.media, str):
                if os.path.isfile(i.media):
                    media = await client.invoke(
                        raw.functions.messages.UploadMedia(
                            peer=await client.resolve_peer(chat_id),
                            media=raw.types.InputMediaUploadedPhoto(
                                file=await client.save_file(i.media)
                            )
                        )
                    )

                    media = raw.types.InputMediaPhoto(
                        id=raw.types.InputPhoto(
                            id=media.photo.id,
                            access_hash=media.photo.access_hash,
                            file_reference=media.photo.file_reference
                        )
                    )
                elif re.match("^https?://", i.media):
                    media = await client.invoke(
                        raw.functions.messages.UploadMedia(
                            peer=await client.resolve_peer(chat_id),
                            media=raw.types.InputMediaPhotoExternal(
                                url=i.media
                            )
                        )
                    )

                    media = raw.types.InputMediaPhoto(
                        id=raw.types.InputPhoto(
                            id=media.photo.id,
                            access_hash=media.photo.access_hash,
                            file_reference=media.photo.file_reference
                        )
                    )
                else:
                    media = utils.get_input_media_from_file_id(i.media, FileType.PHOTO)
            else:
                media = await client.invoke(
                    raw.functions.messages.UploadMedia(
                        peer=await client.resolve_peer(chat_id),
                        media=raw.types.InputMediaUploadedPhoto(
                            file=await client.save_file(i.media)
                        )
                    )
                )

                media = raw.types.InputMediaPhoto(
                    id=raw.types.InputPhoto(
                        id=media.photo.id,
                        access_hash=media.photo.access_hash,
                        file_reference=media.photo.file_reference
                    )
                )
        elif isinstance(i, types.InputMediaVideo):
            if isinstance(i.media, str):
                if os.path.isfile(i.media):
                    media = await client.invoke(
                        raw.functions.messages.UploadMedia(
                            peer=await client.resolve_peer(chat_id),
                            media=raw.types.InputMediaUploadedDocument(
                                file=await client.save_file(i.media),
                                thumb=await client.save_file(i.thumb),
                                mime_type=client.guess_mime_type(i.media) or "video/mp4",
                                attributes=[
                                    raw.types.DocumentAttributeVideo(
                                        supports_streaming=i.supports_streaming or None,
                                        duration=i.duration,
                                        w=i.width,
                                        h=i.height
                                    ),
                                    raw.types.DocumentAttributeFilename(file_name=os.path.basename(i.media))
                                ]
                            )
                        )
                    )

                    media = raw.types.InputMediaDocument(
                        id=raw.types.InputDocument(
                            id=media.document.id,
                            access_hash=media.document.access_hash,
                            file_reference=media.document.file_reference
                        )
                    )
                elif re.match("^https?://", i.media):
                    media = await client.invoke(
                        raw.functions.messages.UploadMedia(
                            peer=await client.resolve_peer(chat_id),
                            media=raw.types.InputMediaDocumentExternal(
                                url=i.media
                            )
                        )
                    )

                    media = raw.types.InputMediaDocument(
                        id=raw.types.InputDocument(
                            id=media.document.id,
                            access_hash=media.document.access_hash,
                            file_reference=media.document.file_reference
                        )
                    )
                else:
                    media = utils.get_input_media_from_file_id(i.media, FileType.VIDEO)
            else:
                media = await client.invoke(
                    raw.functions.messages.UploadMedia(
                        peer=await client.resolve_peer(chat_id),
                        media=raw.types.InputMediaUploadedDocument(
                            file=await client.save_file(i.media),
                            thumb=await client.save_file(i.thumb),
                            mime_type=client.guess_mime_type(getattr(i.media, "name", "video.mp4")) or "video/mp4",
                            attributes=[
                                raw.types.DocumentAttributeVideo(
                                    supports_streaming=i.supports_streaming or None,
                                    duration=i.duration,
                                    w=i.width,
                                    h=i.height
                                ),
                                raw.types.DocumentAttributeFilename(file_name=getattr(i.media, "name", "video.mp4"))
                            ]
                        )
                    )
                )

                media = raw.types.InputMediaDocument(
                    id=raw.types.InputDocument(
                        id=media.document.id,
                        access_hash=media.document.access_hash,
                        file_reference=media.document.file_reference
                    )
                )
        elif isinstance(i, types.InputMediaAudio):
            if isinstance(i.media, str):
                if os.path.isfile(i.media):
                    media = await client.invoke(
                        raw.functions.messages.UploadMedia(
                            peer=await client.resolve_peer(chat_id),
                            media=raw.types.InputMediaUploadedDocument(
                                mime_type=client.guess_mime_type(i.media) or "audio/mpeg",
                                file=await client.save_file(i.media),
                                thumb=await client.save_file(i.thumb),
                                attributes=[
                                    raw.types.DocumentAttributeAudio(
                                        duration=i.duration,
                                        performer=i.performer,
                                        title=i.title
                                    ),
                                    raw.types.DocumentAttributeFilename(file_name=os.path.basename(i.media))
                                ]
                            )
                        )
                    )

                    media = raw.types.InputMediaDocument(
                        id=raw.types.InputDocument(
                            id=media.document.id,
                            access_hash=media.document.access_hash,
                            file_reference=media.document.file_reference
                        )
                    )
                elif re.match("^https?://", i.media):
                    media = await client.invoke(
                        raw.functions.messages.UploadMedia(
                            peer=await client.resolve_peer(chat_id),
                            media=raw.types.InputMediaDocumentExternal(
                                url=i.media
                            )
                        )
                    )

                    media = raw.types.InputMediaDocument(
                        id=raw.types.InputDocument(
                            id=media.document.id,
                            access_hash=media.document.access_hash,
                            file_reference=media.document.file_reference
                        )
                    )
                else:
                    media = utils.get_input_media_from_file_id(i.media, FileType.AUDIO)
            else:
                media = await client.invoke(
                    raw.functions.messages.UploadMedia(
                        peer=await client.resolve_peer(chat_id),
                        media=raw.types.InputMediaUploadedDocument(
                            mime_type=client.guess_mime_type(getattr(i.media, "name", "audio.mp3")) or "audio/mpeg",
                            file=await client.save_file(i.media),
                            thumb=await client.save_file(i.thumb),
                            attributes=[
                                raw.types.DocumentAttributeAudio(
                                    duration=i.duration,
                                    performer=i.performer,
                                    title=i.title
                                ),
                                raw.types.DocumentAttributeFilename(file_name=getattr(i.media, "name", "audio.mp3"))
                            ]
                        )
                    )
                )

                media = raw.types.InputMediaDocument(
                    id=raw.types.InputDocument(
                        id=media.document.id,
                        access_hash=media.document.access_hash,
                        file_reference=media.document.file_reference
                    )
                )
        elif isinstance(i, types.InputMediaDocument):
            if isinstance(i.media, str):
                if os.path.isfile(i.media):
                    media = await client.invoke(
                        raw.functions.messages.UploadMedia(
                            peer=await client.resolve_peer(chat_id),
                            media=raw.types.InputMediaUploadedDocument(
                                mime_type=client.guess_mime_type(i.media) or "application/zip",
                                file=await client.save_file(i.media),
                                thumb=await client.save_file(i.thumb),
                                attributes=[
                                    raw.types.DocumentAttributeFilename(file_name=os.path.basename(i.media))
                                ]
                            )
                        )
                    )

                    media = raw.types.InputMediaDocument(
                        id=raw.types.InputDocument(
                            id=media.document.id,
                            access_hash=media.document.access_hash,
                            file_reference=media.document.file_reference
                        )
                    )
                elif re.match("^https?://", i.media):
                    media = await client.invoke(
                        raw.functions.messages.UploadMedia(
                            peer=await client.resolve_peer(chat_id),
                            media=raw.types.InputMediaDocumentExternal(
                                url=i.media
                            )
                        )
                    )

                    media = raw.types.InputMediaDocument(
                        id=raw.types.InputDocument(
                            id=media.document.id,
                            access_hash=media.document.access_hash,
                            file_reference=media.document.file_reference
                        )
                    )
                else:
                    media = utils.get_input_media_from_file_id(i.media, FileType.DOCUMENT)
            else:
                media = await client.invoke(
                    raw.functions.messages.UploadMedia(
                        peer=await client.resolve_peer(chat_id),
                        media=raw.types.InputMediaUploadedDocument(
                            mime_type=client.guess_mime_type(
                                getattr(i.media, "name", "file.zip")
                            ) or "application/zip",
                            file=await client.save_file(i.media),
                            thumb=await client.save_file(i.thumb),
                            attributes=[
                                raw.types.DocumentAttributeFilename(file_name=getattr(i.media, "name", "file.zip"))
                            ]
                        )
                    )
                )

                media = raw.types.InputMediaDocument(
                    id=raw.types.InputDocument(
                        id=media.document.id,
                        access_hash=media.document.access_hash,
                        file_reference=media.document.file_reference
                    )
                )
        else:
            raise ValueError(f"{i.__class__.__name__} is not a supported type for send_media_group")

        multi_media.append(
            raw.types.InputSingleMedia(
                media=media,
                random_id=client.rnd_id(),
                message=i.caption if i.caption else '',
                entities=i.caption_entities if i.caption_entities else None
            )
        )
        # await client.parser.parse(i.caption, i.parse_mode)
    r = await client.invoke(
        raw.functions.messages.SendMultiMedia(
            peer=await client.resolve_peer(chat_id),
            multi_media=multi_media,
            silent=disable_notification or None,
            reply_to_msg_id=reply_to_message_id,
            schedule_date=utils.datetime_to_timestamp(schedule_date),
            noforwards=protect_content
        ),
        sleep_threshold=60
    )

    return await utils.parse_messages(
        client,
        raw.types.messages.Messages(
            messages=[m.message for m in filter(
                lambda u: isinstance(u, (raw.types.UpdateNewMessage,
                                         raw.types.UpdateNewChannelMessage,
                                         raw.types.UpdateNewScheduledMessage)),
                r.updates
            )],
            users=r.users,
            chats=r.chats
        )
    )
