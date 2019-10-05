<%!
    from datetime import datetime
    from templates.utils import md5file
%>
<!DOCTYPE html>
<html lang="ru-RU">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#157878">
    <link rel="shortcut icon" href="/favicon.ico" type="image/x-icon">
    <link rel="icon" href="/favicon.ico" type="image/x-icon">
    <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.0.12/css/all.css" integrity="sha384-G0fIWCsCzJIMAVNQPfjH08cyYaUtMwjJwqiRKxxE/rx96Uroj1BtIQ6MLJuheaO9" crossorigin="anonymous">
    <link rel="stylesheet" href="/static/css/bootstrap.min.css?hash=${md5file('static/css/bootstrap.min.css')}">
    <link rel="stylesheet" href="/static/css/styles.css?hash=${md5file('static/css/styles.css')}">
    <%block name="head" />
    <script src="https://cdn.jsdelivr.net/npm/intersection-observer@0.5.1/intersection-observer.js"></script>
    <script src="/static/js/matomo.js?hash=${md5file(_('static/js/matomo.js'))}"></script>
  </head>
  <body>
    <div style="height: 56px"><!-- floating navbar workaround --></div>
    <nav class="navbar headroom fixed-top navbar-expand-md navbar-dark bg-dark">
      <div class="container">
        <a class="navbar-brand d-none d-sm-block" href="/">${config['title']}</a>
        <a class="navbar-brand d-sm-none d-block" href="/">${config['title_short']}</a>
        <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbar-collapse" aria-controls="navbar-collapse" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navbar-collapse">
          <ul class="navbar-nav mr-auto">
            <li class="nav-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Категории</a>
              <div class="dropdown-menu" aria-labelledby="navbarDropdown">
              % for i, category in enumerate(categories.values()):
                % if category.level == 2:
                  % if i > 0:
                    <div class="dropdown-divider"></div>
                  % endif
                  <a class="dropdown-item" href="/#${category.code}"><b>${category.name}</b></a>
                % else:
                  <a class="dropdown-item" href="/#${category.code}">${category.name}</a>
                % endif
              % endfor
                <div class="dropdown-divider"></div>
                <a class="dropdown-item" href="/missing.html">Стримы без официальных записей</a>
              </div>
            </li>
          </ul>

          <form class="form-inline" autocomplete="off" action="#">
            <input class="form-control" type="search" id="search" placeholder="Быстрый переход" aria-label="Search">
          </form>
        </div>
      </div>
    </nav>

    <div class="container main-content">
      <%block name="content" />
    </div>

    <footer class="page-footer font-small bg-dark text-white pt-4 mt-4">
      <div class="container">
        <div class="row">
          <div class="col-md-6">
            <h5 class="text-uppercase">Полезные ссылки</h5>
            <ul class="list-unstyled">
              <li>
                <a href="https://github.com/${config['github']['user']}/${config['github']['repo']}/">
                  <i class="fab fa-github"></i> Репозиторий GitHub
                </a>
              </li>
              <li>
                <a href="https://t.me/BlackUFA_Monitor">
                  <i class="fab fa-telegram"></i> Канал BlackUFA_Monitor
                </a>
              </li>
              <li>
                <a href="https://matomo.thedrhax.pw/index.php?module=CoreAdminHome&action=optOut&language=ru">
                  Отказ от участия в статистике сайта
                </a>
              </li>
            </ul>
          </div>
          <div class="col-lg-3 col-md-6">
            <h5 class="text-uppercase">Каналы Артура</h5>
            <ul class="list-unstyled">
              <li>
                <a href="https://www.youtube.com/user/BlackSilverUFA">
                  <i class="fab fa-youtube"></i> BlackSilverUFA
                </a>
              </li>
              <li>
                <a href="https://www.youtube.com/user/BlackSilverChannel">
                  <i class="fab fa-youtube"></i> BlackSilverChannel
                </a>
              </li>
              <li>
                <a href="https://www.twitch.tv/blackufa/">
                  <i class="fab fa-twitch"></i> BlackUFA
                </a>
              </li>
            </ul>
          </div>
          <div class="col-lg-3 col-md-6">
            <h5 class="text-uppercase">Социальные сети</h5>
            <ul class="list-unstyled">
              <li>
                <li>
                  <a href="https://vk.com/b_silver">
                    <i class="fab fa-vk"></i> Группа ВКонтакте
                  </a>
                </li>
                <li>
                  <a href="https://vk.com/blacksilverufa">
                    <i class="fab fa-vk"></i> Страница ВКонтакте
                  </a>
                </li>
                <li>
                  <a href="https://twitter.com/Sempai_Black">
                    <i class="fab fa-twitter"></i> Twitter
                  </a>
                </li>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="footer-copyright py-3 text-center small">
        <i class="far fa-copyright"></i> 2017-${datetime.now().strftime('%Y')}, Дмитрий Карих. Весь контент принадлежит Артуру Блэку. Разрешение на его обработку предоставлено в <a href="https://www.youtube.com/watch?v=Bxj09aAOFaI&lc=UgwQmdNhl4TMNn9-Gg94AaABAg.8ZY93MRq32E8ZY9W3KGSJS">комментарии</a> (<a href="/static/images/answer.jpg">скриншот</a>).
      </div>
    </footer>

    <!-- https://github.com/verlok/lazyload -->
    <script src="https://cdn.jsdelivr.net/npm/vanilla-lazyload@12.0.0/dist/lazyload.min.js"></script>
    <!-- https://github.com/thednp/bootstrap.native -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap.native/2.0.15/bootstrap-native-v4.min.js"></script>
    <!-- https://github.com/sandoche/Darkmode.js -->
    <script src="https://cdn.jsdelivr.net/npm/darkmode-js@1.4.0/lib/darkmode-js.min.js"></script>
    <!-- https://github.com/WickyNilliams/headroom.js -->
    <script src="https://npmcdn.com/headroom.js@0.9.4/dist/headroom.min.js"></script>
    <!-- https://github.com/kraaden/autocomplete -->
    <script src="/static/js/autocomplete.js?hash=${md5file('static/js/autocomplete.js')}"></script>
    <script src="/search.js?hash=${md5file(_('search.js'))}"></script>
    <script type="text/javascript">
      var darkmode = new Darkmode({
        saveInCookies: true,
        label: '<i class="fas fa-lightbulb"></i>',
        autoMatchOsTheme: true
      });
      darkmode.showWidget();

      // Workaround for https://github.com/sandoche/Darkmode.js/issues/7
      document.querySelector('.darkmode-toggle').addEventListener('click', function(e) {
        this.style.pointerEvents = 'none';
        setTimeout(() => {
          this.style.pointerEvents = '';
        }, 500);
      });

      var headroom  = new Headroom(document.querySelector('nav'), {
        onPin: function() {
          darkmode.button.hidden = false;

          if (!darkmode.isActivated()) {
            darkmode.layer.hidden = false;
          }
        },
        onUnpin: function() {
          darkmode.button.hidden = true;

          if (!darkmode.isActivated()) {
            darkmode.layer.hidden = true;
          }
        }
      });
      headroom.init();

      var lazyload = new LazyLoad({
        elements_selector: ".lazyload"
      });

      Search.init("#search");
    </script>
    <%block name="scripts" />
  </body>
</html>