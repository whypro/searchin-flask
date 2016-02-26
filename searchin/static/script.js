var count_per_req = 10;

/*
function search_papers(key, start, count) {
    var begin = new Date();
    var get_paper_search_result_json_url = "/search/paper/json/"+key+"/?start="+start+"&count="+count;
    $.get(get_paper_search_result_json_url, function(data, status) {
        if (status != "success") {
            alert("文献搜索失败！")
            return;
        }

        var end = new Date();
        var spend = end.getTime() - begin.getTime();
        console.log(spend);

        show_papers(data);

        var ts_sel = $("#paper-time-spend");
        var content = '<p><small>共找到 '+data["total"]+' 条记录，耗时 '+spend+' 毫秒</small></p>';
        if (ts_sel.length > 0)
        {
            ts_sel.html(content);
        } else {
            $("#paper-search-result").before(
                '<div id="paper-time-spend" class="text-center">'+content+'</div>'
            );
        }

        if ($("#paper-more-button").length > 0)
        {
            // 存在
            $("#paper-more-button").button('reset');
            $("#paper-more-button").off('click');
            $("#paper-more-button").on('click', function() {
                $(this).button('loading');
                search_papers(key, data["start"]+data['count'], count_per_req)
            });
        }
        else {
            $("#paper-search-result").after(
                '<button type="button" class="btn btn-default btn-block" id="paper-more-button" data-loading-text="加载中……">'+
                    '加载更多'+
                '</button>'
            );
            $("#paper-more-button").off('click');
            $("#paper-more-button").on('click', function() {
                $(this).button('loading');
                search_papers(key, data["start"]+data['count'], count_per_req)
            });
        }
    });
}
*/


function search_papers(key, start, count) {
    var begin = new Date();
    var get_paper_search_result_json_url = "/search/paper/json/"+key+"/?start="+start+"&count="+count;
    $.get(get_paper_search_result_json_url, function(data, status) {
        if (status != "success") {
            alert("文献搜索失败！")
            return;
        }

        var end = new Date();
        var spend = end.getTime() - begin.getTime();
        console.log(spend);

        show_papers(data);

        var ts_sel = $("#paper-time-spend");
        var content = '<p><small>在百度学术中共找到 '+data["total"]+' 条记录，耗时 '+spend+' 毫秒</small></p>';
        if (ts_sel.length > 0)
        {
            ts_sel.html(content);
        } else {
            $("#paper-search-result").before(
                '<div id="paper-time-spend" class="text-center">'+content+'</div>'
            );
        }

        /*
        if (data['count'] < count) {
            $("#paper-more-button").text("没有更多了");
        } else {
            $("#paper-more-button").text("加载更多");
        }
        */
    });
}


function search_books(key, start, count) {
    var begin = new Date();
    var get_book_search_result_json_url = "/search/book/json/"+key+"/?start="+start+"&count="+count;
    $.get(get_book_search_result_json_url, function(data, status) {
        if (status != "success") {
            alert("文献搜索失败！")
            return;
        }

        var end = new Date();
        var spend = end.getTime() - begin.getTime();
        console.log(spend);

        show_books(data);

        var ts_sel = $("#book-time-spend");
        var content = '<p><small>共找到 '+data["total"]+' 条记录，耗时 '+spend+' 毫秒</small></p>';
        if (ts_sel.length > 0)
        {
            ts_sel.html(content);
        } else {
            $("#book-search-result").before(
                '<div id="book-time-spend" class="text-center">'+content+'</div>'
            );
        }

        /*
        if (data['count'] < count) {
            $("#book-more-button").text("没有更多了");
        } else {
            $("#book-more-button").text("加载更多");
        }
        */

        if ($("#book-more-button").length > 0)
        {
            // 存在
            $("#book-more-button").button("reset");
            $("#book-more-button").off("click");
            $("#book-more-button").on("click", function() {
                $(this).button("loading");
                search_books(key, data["start"]+data['count'], count_per_req)
            });
        }
        else {
            $("#book-search-result").after(
                '<button type="button" class="btn btn-default btn-block" id="book-more-button" data-loading-text="加载中……">'+
                    '加载更多'+
                '</button>'
            );
            $("#book-more-button").off("click");
            $("#book-more-button").on("click", function() {
                $(this).button("loading");
                search_books(key, data["start"]+data["count"], count_per_req)
            });
        }
    });
}


/*
function show_papers(data)
{
    var papers = data["papers"]
    for (var i in papers) {
        var url = papers[i]["url"];
        var quoted_url = papers[i]["quoted_url"];
        var title = papers[i]["title"];
        var key_words = papers[i]["key_words"];
        var area = papers[i]["area"];
        var journal = papers[i]["journal"];
        var authors = papers[i]["authors"];
        var year = papers[i]["year"];
        var cite_num = papers[i]["cite_num"];
        var click_num = papers[i]["click_num"];
        var relevancy = papers[i]["relevancy"].toFixed(2);

        $("#paper-search-result").append(
            '<div class="list-group-item">'+
            '    <h4 class="list-group-item-heading">'+
            '        <a href="'+'/redirect/?type=paper&url='+quoted_url+'" target="_blank">'+title+'</a>'+
            '    </h4>'+
            '    <p class="list-group-item-text">'+
            '        关键词：'+key_words.join(", ")+'<br />'+
            '        领域：'+area+'<br />'+
            '        期刊：'+journal+'<br />'+
            '        作者：'+authors.join(", ")+'<br />'+
            '        年份：'+year+'<br />'+
            '        相关度：'+relevancy+'<br />'+
            '        点击量：'+click_num+
            '    </p>'+
            '</div>'
        );
    }
}
*/


function show_papers(data)
{
    var papers = data["papers"]
    for (var i in papers) {
        var scholar_url = papers[i]["scholar_url"];
        var quoted_url = papers[i]["quoted_url"];
        var title = papers[i]["title"][0];
        // var key_words = papers[i]["key_words"];
        // var area = papers[i]["area"];
        var journals = papers[i]["publish"];
        var authors = papers[i]["author"];
        var year = papers[i]["year"][0];
        var cite_num = papers[i]["cited"][0];
        // var click_num = papers[i]["click_num"];
        // var relevancy = papers[i]["relevancy"].toFixed(2);

        $("#paper-search-result").append(
            '<div class="list-group-item text-right">'+
            '    <h4 class="list-group-item-heading">'+
            '        <a href="'+'/redirect/?type=paper&url='+quoted_url+'" target="_blank">'+title+'</a>'+
            '    </h4>'+
            '    <p class="list-group-item-text">'+
            '        期刊：'+journals[0]+'<br />'+
            '        作者：'+authors[0]+'<br />'+
            '        年份：'+year+'<br />'+
            '        引用：'+cite_num+'<br />'+
            '    </p>'+
            '</div>'
        );
    }
}


function show_books(data)
{
    var books = data["books"]
    for (var i in books) {
        var url = books[i]["url"];
        var title = books[i]["title"];
        var image = books[i]["image"];
        var authors = books[i]["authors"];
        var publisher = books[i]["publisher"];
        var year = books[i]["year"];
        // var pages = books[i]["pages"];
        var isbn = books[i]["isbn"];
        var price = books[i]["price"];
        var summary = books[i]["summary"];
        var douban_summary = books[i]["douban_summary"]
        var click_num = books[i]["click_num"];

        $("#book-search-result").append(
            '<div class="list-group-item">'+
            '    <h4 class="list-group-item-heading">'+
            '        <a href="'+'/redirect/?type=book&url='+url+'" target="_blank">'+title+'</a>'+
            '    </h4>'+
            '    <p class="list-group-item-text">'+
            '        <img id="img-'+isbn+'" class="pull-right" height="120px">'+
            '        作者：'+authors+'<br />'+
            '        出版社：'+publisher+'<br />'+
            '        出版时间：'+year+'<br />'+
            // '        页数：'+pages+'<br />'+
            '        ISBN: '+isbn+'<br />'+
            '        定价：'+price+'<br />'+
            '        点击量：'+click_num+'<br />'+
            // '        摘要：'+(summary == undefined ? "无" : summary)+
            // '        摘要：'+(douban_summary == undefined ? "无" : douban_summary)+
            '    </p>'+
            '</div>'
        );

        $.get("/image/"+isbn, function (data){
            // alert(data["url"]);
            $("#img-"+data["isbn"]).attr("src", data["url"]);
        });
    }
}


function search() {
    // $("#search-button").button("loading");
    var key = encodeURIComponent($("#search-input").val().replace(/(\/|\n|\r|\t)/g, ""));
    search_papers(key, 0, count_per_req);
    search_books(key, 0, count_per_req);
}


$(document).ready(function() {

    $("#search-form").submit(function(e) {
        e.preventDefault();
        $("#paper-search-result").empty();
        $("#book-search-result").empty();
        $("#paper-more-button").remove();
        $("#book-more-button").remove();
        $("#paper-time-spend").remove();
        $("#book-time-spend").remove();

        $("#top-br").remove();
        $("#bottom-br").remove();
        search();
    });

});
