(function(){
  var yearEls = document.querySelectorAll('.js-year');
  var year = new Date().getFullYear();
  yearEls.forEach(function(el){ el.textContent = year; });

  var toggle = document.querySelector('.mobile-nav-toggle');
  var mobileNav = document.querySelector('.mobile-nav');
  if(toggle && mobileNav){
    toggle.addEventListener('click', function(){
      mobileNav.classList.toggle('open');
    });
    mobileNav.querySelectorAll('a').forEach(function(a){
      a.addEventListener('click', function(){ mobileNav.classList.remove('open'); });
    });
  }

  // Network / blockchain-style background animation
  var canvas = document.getElementById('netCanvas');
  if(!canvas) return;
  var ctx = canvas.getContext('2d');
  var w, h, nodes;

  function resize(){
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }
  function initNodes(){
    var count = Math.min(70, Math.floor((w*h)/22000));
    nodes = Array.from({length: count}, function(){
      return {
        x: Math.random()*w,
        y: Math.random()*h,
        vx: (Math.random()-0.5)*0.3,
        vy: (Math.random()-0.5)*0.3
      };
    });
  }
  function tick(){
    ctx.clearRect(0,0,w,h);
    for(var i=0;i<nodes.length;i++){
      var n = nodes[i];
      n.x += n.vx; n.y += n.vy;
      if(n.x < 0 || n.x > w) n.vx *= -1;
      if(n.y < 0 || n.y > h) n.vy *= -1;
    }
    for(var a=0;a<nodes.length;a++){
      for(var b=a+1;b<nodes.length;b++){
        var na = nodes[a], nb = nodes[b];
        var dx = na.x-nb.x, dy = na.y-nb.y;
        var dist = Math.sqrt(dx*dx+dy*dy);
        if(dist < 140){
          ctx.strokeStyle = 'rgba(53,224,161,' + (0.12 * (1 - dist/140)) + ')';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(na.x, na.y);
          ctx.lineTo(nb.x, nb.y);
          ctx.stroke();
        }
      }
    }
    for(var c=0;c<nodes.length;c++){
      var nn = nodes[c];
      ctx.fillStyle = 'rgba(53,224,161,0.55)';
      ctx.beginPath();
      ctx.arc(nn.x, nn.y, 1.6, 0, Math.PI*2);
      ctx.fill();
    }
    requestAnimationFrame(tick);
  }
  window.addEventListener('resize', function(){ resize(); initNodes(); });
  resize(); initNodes(); tick();
})();
