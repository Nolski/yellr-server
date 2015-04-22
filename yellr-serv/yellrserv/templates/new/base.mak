<tml>
<head>

  <title>Yellr - Hyper-local, community driven news</title>

  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <link rel="stylesheet" href="static/new/foundation/css/foundation.css" />
  <!--<link rel="stylesheet" href="static/new/css/font-awesome.min.css" />-->
  <!-- TODO: pull this from our server locally -->
  <link rel="stylesheet" href="//maxcdn.bootstrapcdn.com/font-awesome/4.3.0/css/font-awesome.min.css">
  <link rel="stylesheet" href="static/new/css/site.css" />

</head>
<body>

  <div class="site-wrapper">

    <script src="static/new/foundation/js/vendor/jquery.js"></script>

    <!--
    <header class="about-bar">
      <div class="row">
        <div class="large-12 columns">
          <div class="right">
            <a href="/about">About</a>
          </div>
          <div>
            <a href="/">Home</a>
          </div>
        </div>
      
    </header>
    -->

    <header class="yellr-site-header">
      <div class="row">
        <div class="columns">
          <a href="/"><h1>Yellr</h1></a>
          <p>Rochester, New York <br/><small>B E T A</small></p>
        </div>
      </div>
    </header>

    <div class="row">
      <div class="large-12 columns">
        ${self.body()}
      </div>
    </div>

    <footer>
      <div class="row">
        <div class="medium-12 columns">
          <div class="footer">
            <a href="https://yellr.net/">Yellr</a> | Copyright 2015 | <a href="http://wxxinews.org/">WXXI</a> | <a href="http://www.meetup.com/HackshackersROC/">Hacks/Hackers Rochester</a> | <a href="github.com/hhroc/yellr-server">Source</a> 
          </div>
        </div>
      </div>
    </footer>


  </div>

  <script src="static/new/foundation/js/foundation/foundation.js"></script>
  <script src="static/new/foundation/js/vendor/modernizr.js"></script>

  <script>
    $(document).foundation();

    $(document).ready(function() {
      var c = getCookie('cuid');
      if ( c == '' ) {
        setCookie('cuid', '${cuid}', 365*10);
      } 
    });

    // functions taken from
    //   http://www.w3schools.com/js/js_cookies.asp
    function setCookie(cname, cvalue, exdays) {
      var d = new Date();
      d.setTime(d.getTime() + (exdays*24*60*60*1000));
      var expires = "expires="+d.toUTCString();
      document.cookie = cname + "=" + cvalue + "; " + expires;
    }
    function getCookie(cname) {
      var name = cname + "=";
      var ca = document.cookie.split(';');
      for(var i=0; i<ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1);
        if (c.indexOf(name) == 0) return c.substring(name.length,c.length);
      }
      return "";
    }
  </script>

</body>
</html>