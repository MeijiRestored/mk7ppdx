$(window).ready(function(){
  $('.menu-toggle').click(function(){
    $('.main-nav').toggleClass('main-nav-open',500);
    $(this).toggleClass('open');
  });
});
