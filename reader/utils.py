import datetime
import hashlib
import time

def get_story_content(data):
    if 'content' in data:
        return data['content'][0]['value'].strip()
    elif 'summary' in data:
        return data['summary'].strip()
    return u''

def get_story_date(data):
    if 'published_parsed' in data:
        return datetime.datetime.fromtimestamp(time.mktime(data['published_parsed']))
    elif 'updated_parsed' in data:
        return datetime.datetime.fromtimestamp(time.mktime(data['updated_parsed']))
    return datetime.datetime.now()

def get_story_identifier(feed, data):
    bits = [
        feed.url,
        get_story_date(data).strftime('%Y-%m-%d %H:%M:%S'),
    ]
    if 'link' in data:
        bits.append(data['link'])
    if 'id' in data:
        bits.append(data['id'])
    return hashlib.sha1('\n'.join(bits)).hexdigest()

def get_stories(feeds, user):
    from reader.models import Story
    sql = """
        SELECT
            s.*,
            coalesce(rs.is_read, 0) AS "is_read",
            coalesce(rs.is_starred, 0) AS "is_starred",
            coalesce(rs.notes, '') AS "notes"
        FROM
            reader_story s
            LEFT OUTER JOIN reader_readstory rs ON rs.story_id = s.id AND rs.user_id = %(user_id)s
        WHERE
            s.feed_id IN (%(feed_ids)s)
    """
    params = {
        'feed_ids': ', '.join([str(f.pk) for f in feeds]),
        'user_id': user.pk,
    }
    return Story.objects.raw(sql % params)

def ajaxify(model, fields=None, extra=None):
    if fields is None:
        fields = [f.name for f in model._meta.fields]
    if extra:
        fields = list(fields) + list(extra)
    data = {}
    for field_name in fields:
        obj = getattr(model, field_name, None)
        if hasattr(obj, 'pk'):
            data[field_name] = obj.pk
        elif isinstance(obj, datetime.datetime):
            data[field_name] = obj.isoformat()
        elif callable(obj):
            data[field_name] = obj()
        else:
            data[field_name] = obj
    if hasattr(model, 'get_absolute_url'):
        data['reader_url'] = model.get_absolute_url()
    return data