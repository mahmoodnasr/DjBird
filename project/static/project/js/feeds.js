$(function () {
  var page_title = $(document).attr("title");

  function hide_stream_update() {
    $(".stream-update").hide();
    $(".stream-update .new-posts").text("");
    $(document).attr("title", page_title);
  };


  $(".btn-compose").click(function () {
    if ($(".compose").hasClass("composing")) {
      $(".compose").removeClass("composing");
      $(".compose").slideUp();
    }
    else {
      $(".compose").addClass("composing");
      $(".compose textarea").val("");
      $(".compose").slideDown(400, function () {
        $(".compose textarea").focus();
      });
    }
  });

  $(".btn-cancel-compose").click(function () {
    $(".compose").slideUp();
  });

  $(".btn-post").click(function () {
    var last_feed = $(".stream li:first-child").attr("feed-id");
    if (last_feed == undefined) {
      last_feed = "0";
    }
    $("#compose-form input[name='last_feed']").val(last_feed);
    $.ajax({
      url: '/feeds/post/',
      data: $("#compose-form").serialize(),
      type: 'post',
      cache: false,
      success: function (data) {
        $("ul.stream").prepend(data);
        $(".compose").slideUp();
        $(".compose").removeClass("composing");
        hide_stream_update();
      }
    });
  });

  $("ul.stream").on("click", ".like", function () {
    var li = $(this).closest("li");
    var feed = $(li).attr("feed-id");
    var csrf = $(li).attr("csrf");
    $.ajax({
      url: '/feeds/like/',
      data: {
        'feed': feed,
        'csrfmiddlewaretoken': csrf
      },
      type: 'post',
      cache: false,
      success: function (data) {
        if ($(".like", li).hasClass("unlike")) {
          $(".like", li).removeClass("unlike");
          $(".like .text", li).text("Like");
        }
        else {
          $(".like", li).addClass("unlike");
          $(".like .text", li).text("Unlike");
        }
        $(".like .like-count", li).text(data);
      }
    });
    return false;
  });

  $("ul.stream").on("click", ".comment", function () { 
    var post = $(this).closest(".post");
    if ($(".comments", post).hasClass("tracking")) {
      $(".comments", post).slideUp();
      $(".comments", post).removeClass("tracking");
    }
    else {
      $(".comments", post).show();
      $(".comments input[name='post']", post).focus();
      var feed = $(post).closest("li").attr("feed-id");
      $.ajax({
        url: '/feeds/comment/',
        data: { 'feed': feed },
        cache: false,
        beforeSend: function () {
          $("ol", post).html("<li class='loadcomment'><img src='/static/project/img/loading.gif'></li>");
        },
        success: function (data) {
          $("ol", post).html(data);
          $(".comment-count", post).text($("ol li", post).not(".empty").length);
        }
      });
    }
    return false;
  });

  $("ul.stream").on("keydown", ".comments input[name='post']", function (evt) {
    var keyCode = evt.which?evt.which:evt.keyCode;
    if (keyCode == 13) {//Enter
      var form = $(this).closest("form");
      var container = $(this).closest(".comments");
      var input = $(this);
      $.ajax({
        url: '/feeds/comment/',
        data: $(form).serialize(),
        type: 'post',
        cache: false,
        beforeSend: function () {
          $(input).val("");
        },
        success: function (data) {
          $("ol", container).html(data);
          var post_container = $(container).closest(".post");
          $(".comment-count", post_container).text($("ol li", container).length);
        }
      });
      return false;
    }
  });

  var load_feeds = function () {
    if (!$("#load_feed").hasClass("no-more-feeds")) {
      var page = $("#load_feed input[name='page']").val();
      var next_page = parseInt($("#load_feed input[name='page']").val()) + 1;
      $("#load_feed input[name='page']").val(next_page);
      $.ajax({
        url: '/feeds/load/',
        data: $("#load_feed").serialize(),
        cache: false,
        beforeSend: function () {
          $(".load").show();
        },
        success: function (data) {
          if (data.length > 0) {
            $("ul.stream").append(data)
          }
          else {
            $("#load_feed").addClass("no-more-feeds");
          }
        },
        complete: function () {
          $(".load").hide();
        }
      });
    }
  };


  $("input,textarea").attr("autocomplete", "off");


  $("ul.stream").on("click", ".remove-feed", function () {
    var li = $(this).closest("li");
    var feed = $(li).attr("feed-id");
    var csrf = $(li).attr("csrf");
    $.ajax({
      url: '/feeds/remove/',
      data: {
        'feed': feed,
        'csrfmiddlewaretoken': csrf
      },
      type: 'post',
      cache: false,
      success: function (data) {
        $(li).fadeOut(400, function () {
          $(li).remove();
        });
      }
    });
  });

  $("#compose-form textarea[name='post']").keyup(function () {
    $(this).count(250);
  });

});
