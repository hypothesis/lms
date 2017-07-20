
var output = '';
var displayed_in_thread = [];
var query = 'https://hypothes.is/api/search?limit=200&offset=__OFFSET__';

function all_activity_for(user) {
   var activity_url = 'http://jonudell.net/h/facet.html?facet=user&search=' + user;
   document.getElementById('all_activity_href').href = activity_url;
   document.getElementById('all_activity_user').innerText = user;
}

var token_ux = function(){/*
<p>
<input onchange="javascript:set_token()" type="password" value="" size="40" id="token"> <span class="small">(for private group annotations, include your <a target="token" href="https://hypothes.is/profile/developer">API token</a>)</span> 
</p>
*/};

function show_token_ux() {
    document.querySelector('#token_ux').innerHTML = heredoc(token_ux);
    token = localStorage.getItem('h_token');
    document.querySelector('#token').value = token;
}

var see_all_ux = function(){/*
<p>Below you'll see Hypothesis conversations on this document in which <span style="font-weight:bold" id="all_activity_user"></span> participated. (Click <a target="all_activity" id="all_activity_href" href="">here</a> to review all Hypothesis activity for that user.)</p>
*/};

function show_see_all_ux() {
    document.querySelector('#see_all_ux').innerHTML = heredoc(see_all_ux);
}

function load(user, offset, rows, replies) {
    var limit = 400;
    var _query = query.replace('__OFFSET__', offset);
    $.ajax({
        url: _query,
        type: "GET",
        beforeSend: function (xhr) {
            var token = localStorage.getItem('h_token');
            if (token != '') {
                xhr.setRequestHeader('Authorization', 'Bearer ' + token);
                xhr.setRequestHeader('Content-Type', 'application/json;charset=utf-8');
            }
        },
        success: function (data) {
            if (data.hasOwnProperty('rows'))     // capture annotations
                rows = rows.concat(data.rows);
            if (data.hasOwnProperty('replies')) { // also capture replies
                rows = rows.concat(data.replies);
                replies = replies.concat(data.replies);
            }
            if (data.rows.length == 0 || rows.length > limit) {
                process(rows, replies);
                show_token_ux();
                show_see_all_ux();
                all_activity_for(user);
                }
            else
                load(user, offset + 200, rows, replies);
        }
    });
}

function gather(rows) {
    var urls = {};
    var ids = {};
    var titles = {};
    var url_updates = {};
    var annos = {};
    for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
//        if ( ! row.permissions.read[0].startsWith('group') )  // exclude private annotations
//            continue;
        var annotation = parse_annotation(row);  // parse the annotation
        var id = annotation.id;
        annos[id] = annotation;                  // save it by id
        var url = annotation.url;             // remember these things
        url = url.replace(/\/$/, "");            // strip trailing slash
        var updated = annotation.updated;
        var title = annotation.title;
        if (!title)
            title = url;
        if (url in urls) {                     // add/update this url's info
            urls[url] += 1;
            ids[url].push(id);
            if (updated > url_updates[url])
                url_updates[url] = updated;
        }
        else {                                   // init this url's info
            urls[url] = 1;
            ids[url] = [id];
            titles[url] = title;
            url_updates[url] = updated;
        }
    }
    return { ids: ids, url_updates: url_updates, annos: annos, titles: titles, urls: urls };
}

function organize(url_updates) {
    var reverse_chron_urls = [];
    for (var url_update in url_updates)  // sort urls in reverse chron of recent update
        reverse_chron_urls.push([url_update, url_updates[url_update]]);
    reverse_chron_urls.sort(function (a, b) { return new Date(b[1]) - new Date(a[1]) });
    return reverse_chron_urls;
}

var docview_template = function(){/*
<div id="d__INDEX__">
<div class="annotations" id="a__INDEX__">
__THREAD__
</div>
</div>
*/};


function document_view(element, gathered, replies) {
    var url_updates = gathered.url_updates;
    var ids = gathered.ids;
    var titles = gathered.titles;
    var annos = gathered.annos;
    var urls = gathered.urls;
    var reverse_chron_urls = organize(url_updates);


    var elt = $('#' + element);

    for (var i = 0; i < reverse_chron_urls.length; i++) {

        var s = heredoc(docview_template);

        s = s.replace(/__INDEX__/g, i);

        var url = reverse_chron_urls[i][0];
         
        var ids_for_url = ids[url];
        output = ''
        for (var j = 0; j < ids_for_url.length; j++) {
            var id = ids_for_url[j];
            output += '<div id="c' + j + '" class="container">';
            show_thread(annos, id, 0, replies, []);
            output += '</div>';
        }
        s = s.replace(/__THREAD__/, output);
        elt.append(s);
    }
}

function show_thread(annos, id, level, replies) {
    var anno = annos[id];
    if (displayed_in_thread.indexOf(id) == -1 ) {
        var margin = level * 20;
        var dt = new Date(anno['updated']);
        var dt_str = dt.toLocaleDateString() + ' ' + dt.toLocaleTimeString();
        var converter = new Showdown.converter();
        var text = anno['text'] == null ? '' : anno['text'];
        var html = converter.makeHtml(text);
        var options = {
            whiteList: {
                a: ['href', 'title'],
                img: ['alt', 'src'],
                p: [],
                blockquote: [],
                span: ['title', 'class']
            },
            stripIgnoreTag: true,
            stripIgnoreTagBody: ['script']
        };
        html = filterXSS(html, options);
        var tags = '';
        if (anno.tags.length) 
			tags = make_tags(anno.tags);
        var user = anno.user;
        var quote = filterXSS(anno.quote, {});
        var anno_scope = ''
        if ( ! anno.permissions.read[0].startsWith('group') )
            anno_scope = '(Only Me)';
        else if ( anno.permissions.read[0] == 'group:__world__') 
            anno_scope = '(Public)';
        else if ( anno.permissions.read[0].startsWith('group') )
            anno_scope = '(Group <a target="group" href="https://hypothes.is/groups/' + anno.group + '">' + anno.group + '</a>)';

        var template = '<div class="annotation" style="margin-left:_MARGIN_px;">' +
                        '<span class="user"><a target="_user" href="facet.html?facet=user&search=' + user + '">' + user + '</a></span>' + ' ' +
                        '<span class="timestamp">' + dt_str + '</span>' +
                        '<span style="font-size:smaller"><a title="permalink" target="_new" href="https://hyp.is/' + anno.id + '"> # </a></span>' +
                        '<span style="font-size:smaller">' + anno_scope + '</span>' +
                        '<div class="annotation-quote">' + quote + '</div>' +
                        tags +
                        '<div>' + html + '</div>' +
                        '</div>';
        output += template.replace('_MARGIN_', margin);
        displayed_in_thread.push(id);
    }

    var children = replies.filter(function (row) {
        return row.hasOwnProperty('references') && row.references.indexOf(id) != -1;
    });

    children = children.map(function (row) {
        return row.id;
    });

    children.reverse();

    if (children.length) {
        for (var i = 0; i < children.length; i++)
            show_thread(annos, children[i], level + 1, replies);
    }
}

function show_annotation(anno) {
    var margin = 20;
    var dt = new Date(anno.updated);
    var user = anno.user.replace('acct:','').replace('@hypothes.is','')
    user = user;
    var url = anno.url;
    var quote = '';
    if (anno.quote) {
      quote = filterXSS(quote, {});
	  }
    var dt_str = dt.toLocaleDateString() + ' ' + dt.toLocaleTimeString();
    var converter = new Showdown.converter();
    var html = '';
    if (text) {
        html = converter.makeHtml(text);
        html = filterXSS(html, options);
        if ( ! html ) {
            html = '';
        }
    }
    var options = {
        whiteList: {
            a: ['href', 'title'],
            img: ['alt', 'src'],
            p: [],
            blockquote: [],
            span: ['title', 'class']
        },
        stripIgnoreTag: true,
        stripIgnoreTagBody: ['script']
    };
    var tags = '';
    if (anno.tags.length) 
		tags = make_tags(anno.tags);
    var template = '<div class="annotation">' +
        '<span class="user"><a target="_user" href="facet.html?facet=user&search=' + anno.user + '">' + user + '</a></span>' + ' ' +
        '<span class="timestamp">' + dt_str + '</span>' +
        '<span style="font-size:smaller"><a title="permalink" target="_new" href="https://hyp.is/' + anno.id + '"> # </a></span>' +
        '<div><a class="visit" target="visit" href="' + url + '">' + title + '</a></div>' +
        '<div class="url">' + url + '</div>' +
        '<div class="annotation-quote">' + quote + '</div>' +
        tags +
        '<div>' + html + '</div>' +
        '</div>';
    output += template.toString();
}

function parse_annotation(row) {
    var id = row.id;
    var url = row.uri;
    var updated = row.updated.slice(0, 19);
    var group = row.group;
    var title = url;
    var refs = row.hasOwnProperty('references') ? row['references'] : [];
    var user = row.user.replace('acct:', '').replace('@hypothes.is', '');
    var quote = '';
    if ( // sigh...
            row.hasOwnProperty('target') &&
            row.target.length
            ) {
        var selectors = row.target[0]['selector'];
        if (selectors) {
            for (var i = 0; i < selectors.length; i++) {
                selector = selectors[i];
                if (selector.type == 'TextQuoteSelector')
                    quote = selector.exact;
            }
        }
    }
    var text = row.hasOwnProperty('text') ? row.text : '';
    var tags = [];
    try {
        title = row.document.title;
        if ( typeof(title) == 'object' )
            title = title[0];
        refs[id] = refs;
        tags = row.tags;
    }
    catch (e) {
        console.log(e);
    }
    var permissions = row.permissions;
    return {
        id: id,
        url: url,
        updated: updated,
        title: title,
        refs: refs,
        user: user,
        text: text,
        quote: quote,
        tags: tags,
        group: group,
        permissions: permissions
    }
}

function gup(name, str) {
    if (! str) 
        str = window.location.href;
    else
        str = '?' + str;
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regexS = "[\\?&]" + name + "=([^&#]*)";
    var regex = new RegExp(regexS);
    var results = regex.exec(str);
    if (results == null)
        return "";
    else
        return results[1];
}


function getLocalStorageItem(key) {
    var value = localStorage.getItem(key);
    if (value == "null") value = "";
    return value;
}

function add_css(css) {
    var head = document.getElementsByTagName('head')[0];
    var s = document.createElement('style');
    s.setAttribute('type', 'text/css');
    if (s.styleSheet) {   // IE
        s.styleSheet.cssText = css;
    } else {                // the world
        s.appendChild(document.createTextNode(css));
    }
    head.appendChild(s);
}


function heredoc(fn) {
 var a = fn.toString();
 var b = a.slice(14, -3);
 return b;
}


function make_tags(tags) {
  var links = tags.map(function (x) { return '<a target="_tag" href="facet.html?mode=' + mode + '&facet=tag&search=' + x.replace('#', '') + '">' + x + '</a>' });
  var tags = '<div class="tags">' +
      '<span class="tag-item">' +
      links.join('</span><span class="tag-item">') +
      '</span></div>';
  return tags;
}

