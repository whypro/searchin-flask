

function search() {

    var key = encodeURIComponent($("#search-input").val().replace(/(\/|\n|\r|\t)/g, ""));

    var get_paper_search_result_json_url = "/search/paper/json/"+key+"/";
    $.get(get_paper_search_result_json_url, function(data, status) {
        if (status != "success") {
            alert("文献搜索失败！")
            return;
        }

        $("#paper-search-result").empty();

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
                '        <a href="'+url+'" target="_blank">'+title+'</a>'+
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
    });

    var get_book_search_result_json_url = "/search/book/json/"+key+"/";
    $.get(get_book_search_result_json_url, function(data, status) {
        if (status != "success") {
            alert("图书搜索失败！")
            return;
        }

        $("#book-search-result").empty();

        var books = data["books"]
        for (var i in books) {
            var url = books[i]["url"];
            var title = books[i]["title"];
            var image = books[i]["image"];
            var authors = books[i]["author"];
            var publisher = books[i]["publisher"];
            var pubdate = books[i]["pubdate"];
            var pages = books[i]["pages"];
            var isbn13 = books[i]["isbn13"];
            var price = books[i]["price"];
            var summary = books[i]["summary"];
            var click_num = books[i]["click_num"];

            $("#book-search-result").append(
                '<div class="list-group-item text-left">'+
                '    <h4 class="list-group-item-heading">'+
                '        <a href="'+url+'" target="_blank">'+title+'</a>'+
                '    </h4>'+
                '    <p class="list-group-item-text">'+
                '        <img src="'+image+'" class="pull-right" height="120px" />'+
                '        作者：'+authors.join(", ")+'<br />'+
                '        出版社：'+publisher+'<br />'+
                '        出版时间：'+pubdate+'<br />'+
                '        页数：'+pages+'<br />'+
                '        ISBN: '+isbn13+'<br />'+
                '        定价：'+price+'<br />'+
                '        点击量：'+click_num+'<br />'+
                '        摘要：'+summary.slice(0, 120)+'……'+
                '    </p>'+
                '</div>'
            );
        }
    });
}


$(document).ready(function() {

    $("#search-form").submit(function(e) {
        e.preventDefault();
        search();
    });

});


