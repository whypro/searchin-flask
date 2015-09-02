var count_per_req = 10;

function search_papers(key, start, count) {
    var get_paper_search_result_json_url = "/search/paper/json/"+key+"/?start="+start+"&count="+count;
    $.get(get_paper_search_result_json_url, function(data, status) {
        if (status != "success") {
            alert("文献搜索失败！")
            return;
        }

        show_papers(data);

        if (data['count'] < count)
        {
            $("#paper-more-button").text("没有更多了");
            return;
        }
        
        if ($("#paper-more-button").length > 0)
        {
            // 存在
            $("#paper-more-button").button('reset');
            $('#paper-more-button').off('click');
            $('#paper-more-button').on('click', function() {
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
            $('#paper-more-button').off('click');
            $('#paper-more-button').on('click', function() {
                $(this).button('loading');
                search_papers(key, data["start"]+data['count'], count_per_req)
            });
        }
    });
}


function search_books(key, start, count) {
    var get_book_search_result_json_url = "/search/book/json/"+key+"/?start="+start+"&count="+count;
    $.get(get_book_search_result_json_url, function(data, status) {
        if (status != "success") {
            alert("文献搜索失败！")
            return;
        }

        show_books(data);

        if (data["count"] < count)
        {
            $("#book-more-button").text("没有更多了");
            // $("#book-more-button").button("reset");
            // $("#book-more-button").attr("disabled", "disabled");
            return;
        }
        
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


function show_papers(data)
{
    var papers = data["papers"]
    for (var i in papers) {
        var url = papers[i]["url"];
        var title = papers[i]["title"];
        var key_words = papers[i]["key_words"];
        var area = papers[i]["area"];
        var journal = papers[i]["journal"];
        var authors = papers[i]["authors"];
        var year = papers[i]["year"];
        var cite_num = papers[i]["cite_num"];
        var click_num = papers[i]["click_num"];

        $("#paper-search-result").append(
            '<div class="list-group-item text-right">'+
            '    <h4 class="list-group-item-heading">'+
            '        <a href="'+'/redirect/?type=paper&url='+url+'" target="_blank">'+title+'</a>'+
            '    </h4>'+
            '    <p class="list-group-item-text">'+
            '        关键词：'+key_words.join(", ")+'<br />'+
            '        领域：'+area+'<br />'+
            '        期刊：'+journal+'<br />'+
            '        作者：'+authors.join(", ")+'<br />'+
            '        年份：'+year+'<br />'+
            '        引用量：'+cite_num+'<br />'+
            '        点击量：'+click_num+
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
        // var douban_summary = books[i]["douban_summary"]
        var click_num = books[i]["click_num"];

        $("#book-search-result").append(
            '<div class="list-group-item text-left">'+
            '    <h4 class="list-group-item-heading">'+
            '        <a href="'+'/redirect/?type=book&url='+url+'" target="_blank">'+title+'</a>'+
            '    </h4>'+
            '    <p class="list-group-item-text">'+
            // '        <img src="'+image+'" class="pull-right" height="120px" />'+
            '        作者：'+authors+'<br />'+
            '        出版社：'+publisher+'<br />'+
            '        出版时间：'+year+'<br />'+
            // '        页数：'+pages+'<br />'+
            '        ISBN: '+isbn+'<br />'+
            '        定价：'+price+'<br />'+
            '        点击量：'+click_num+'<br />'+
            '        摘要：'+(summary == undefined ? "无" : summary)+
            '    </p>'+
            '</div>'
        );
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
        $("#top-br").remove();
        $("#bottom-br").remove();
        search();
    });

});


