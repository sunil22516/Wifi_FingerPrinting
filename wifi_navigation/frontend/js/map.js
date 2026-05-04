/**
 * Floor Map Renderer — Full 4th Floor (B-Wing + Junction + A-Wing)
 * ================================================================
 * Coordinate system: x=east, y=south, origin=top-left
 *   B-wing:   x=0–58   (B-412 @ x=2, B-401 @ x=55)
 *   Junction: x=58–68  (Open Meeting Area, Lift Lobby)
 *   A-wing:   x=68–122 (A-401 @ x=70, A-412 @ x=118)
 *   Depth:    y=0–22
 * Scale: 8 px/m  |  Canvas: 1060 × 330 px
 */

class FloorMap {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx    = this.canvas.getContext('2d');

        this.canvas.width  = 1060;
        this.canvas.height = 330;

        this.scale   = 8;
        this.offsetX = 20;
        this.offsetY = 35;

        this.nodes           = {};
        this.edges           = [];
        this.userPosition    = null;
        this.destinationNode = null;
        this.navigationPath  = null;

        this.C = {
            wall:'#2d3748', roomFill:'#ebf8ff', roomBorder:'#90cdf4',
            labFill:'#fef3c7', labBorder:'#f6ad55',
            discFill:'#fff5f5', discBorder:'#fc8181',
            liftFill:'#bee3f8', liftBorder:'#3182ce',
            openFill:'#e6fffa', junctFill:'#e9d8fd', corrFill:'#ebf4fd',
            utilFill:'#e2e8f0', edgeLine:'#bee3f8',
            nodeRoom:'#805ad5', nodeLmk:'#d69e2e', nodeCorr:'#a0aec0',
            nodeLabel:'#4a5568', userDot:'#3182ce', userGlow:'rgba(49,130,206,0.25)',
            destPin:'#e53e3e', destGlow:'rgba(229,62,62,0.25)',
            pathLine:'#38a169', pathGlow:'rgba(56,161,105,0.20)',
            text:'#1a202c', textSub:'#718096',
        };

        this.canvas.addEventListener('click', e => this._handleClick(e));
        this.render();
    }

    px(x,y)      { return { px: this.offsetX + x*this.scale, py: this.offsetY + y*this.scale }; }
    world(px,py) { return { x:(px-this.offsetX)/this.scale, y:(py-this.offsetY)/this.scale }; }
    toPixel(x,y) { return this.px(x,y); }
    toWorld(px,py){ return this.world(px,py); }

    async loadGraph() {
        try {
            const r=await fetch('/api/graph'); const d=await r.json();
            if(d.success){ this.nodes=d.nodes; this.edges=d.edges; }
        } catch(e){ console.warn('graph load failed',e); }
        this.render();
    }

    render() {
        const ctx=this.ctx;
        ctx.clearRect(0,0,this.canvas.width,this.canvas.height);
        ctx.fillStyle='#f0f4f8';
        ctx.fillRect(0,0,this.canvas.width,this.canvas.height);
        this._drawFloorPlan();
        this._drawEdges();
        if(this.navigationPath) this._drawPath();
        this._drawNodes();
        if(this.destinationNode) this._drawDest();
        if(this.userPosition)    this._drawUser();
        this._drawScale();
    }

    _drawFloorPlan() {
        const S=this.scale, C=this.C, ctx=this.ctx;

        const R=(x,y,w,h,fill,stroke,lw=1)=>{
            const p=this.px(x,y);
            ctx.fillStyle=fill; ctx.fillRect(p.px,p.py,w*S,h*S);
            ctx.strokeStyle=stroke; ctx.lineWidth=lw; ctx.strokeRect(p.px,p.py,w*S,h*S);
        };
        const T=(x,y,w,h,text,font='7px Segoe UI',color=C.text)=>{
            const cp=this.px(x+w/2,y+h/2);
            ctx.fillStyle=color; ctx.font=font;
            ctx.textAlign='center'; ctx.textBaseline='middle';
            text.split('\n').forEach((l,i,a)=>
                ctx.fillText(l,cp.px,cp.py+(i-(a.length-1)/2)*9));
        };

        // ── B-WING outline ──────────────────────────────────────────────
        R(0,0,58,22,'#f7fafc',C.wall,3);
        R(0,6,58,4,C.corrFill,'transparent');
        R(0,10,2,8,C.utilFill,C.wall,1); T(0,13,2,4,'AHU','6px Segoe UI',C.textSub);
        R(0,18,2,4,'#fce7f3',C.wall,1); T(0,18,2,4,'WC','6px Segoe UI',C.textSub);

        [ {x:0,w:4,l:'B-412'},{x:4,w:4,l:'B-411'},{x:8,w:4,l:'B-410'},
          {x:16,w:4,l:'B-409'},{x:20,w:4,l:'B-408'},{x:24,w:4,l:'B-407'},
          {x:28,w:4,l:'B-406'},{x:32,w:4,l:'B-405'},
          {x:40,w:4,l:'B-404'},{x:44,w:4,l:'B-403'},{x:48,w:4,l:'B-402'},
          {x:52,w:6,l:'B-401'} ].forEach(r=>{
            R(r.x,0,r.w,6,C.roomFill,C.roomBorder);
            T(r.x,0,r.w,6,r.l,'bold 7px Segoe UI');
        });
        R(12,0,4,6,C.openFill,C.roomBorder); T(12,0,4,6,'open','6px Segoe UI',C.textSub);
        R(36,0,4,6,C.openFill,C.roomBorder); T(36,0,4,6,'open','6px Segoe UI',C.textSub);
        R(12,6,4,4,'#d4fce8','transparent'); T(12,6,4,4,'Open\n1B','6px Segoe UI','#276749');
        R(36,6,4,4,'#d4fce8','transparent'); T(36,6,4,4,'Open\n2B','6px Segoe UI','#276749');

        { const p=this.px(1,7.9); ctx.fillStyle=C.textSub; ctx.font='7px Segoe UI';
          ctx.textAlign='left'; ctx.textBaseline='middle';
          ctx.fillText('← 2.4M corridor →',p.px,p.py); }

        [ {x:2,w:8,l:'DCL\nLab',f:C.labFill,b:C.labBorder},
          {x:10,w:10,l:'B-414\nDisc.',f:C.discFill,b:C.discBorder},
          {x:20,w:8,l:'B-415\nLab',f:C.labFill,b:C.labBorder},
          {x:28,w:8,l:'B-416\nLab',f:C.labFill,b:C.labBorder},
          {x:36,w:6,l:'B-417\nOpen',f:C.openFill,b:C.labBorder},
          {x:42,w:8,l:'IRAS\nLab',f:C.labFill,b:C.labBorder},
          {x:50,w:8,l:'B-419\nLab',f:C.labFill,b:C.labBorder} ].forEach(r=>{
            R(r.x,10,r.w,7,r.f,r.b); T(r.x,10,r.w,7,r.l,'bold 7px Segoe UI');
        });

        { const p=this.px(29,0); ctx.fillStyle='#4a5568'; ctx.font='bold 9px Segoe UI';
          ctx.textAlign='center'; ctx.textBaseline='bottom';
          ctx.fillText('B - W I N G',p.px,p.py-3); }

        // ── JUNCTION ────────────────────────────────────────────────────
        R(58,0,10,22,C.junctFill,C.wall,2);
        R(58,0,10,5,'#c6f6d5',C.labBorder,1); T(58,0,10,5,'Open\nMeeting','bold 7px Segoe UI','#22543d');
        R(58,5,10,5,C.liftFill,C.liftBorder,2); T(58,5,10,5,'LIFT\nLobby','bold 8px Segoe UI','#2b6cb0');

        // ── A-WING outline ──────────────────────────────────────────────
        R(68,0,54,22,'#f7fafc',C.wall,3);
        R(68,6,54,4,C.corrFill,'transparent');
        R(120,10,2,8,C.utilFill,C.wall,1); T(120,13,2,4,'AHU','6px Segoe UI',C.textSub);
        R(120,18,2,4,'#fce7f3',C.wall,1); T(120,18,2,4,'WC','6px Segoe UI',C.textSub);

        { const p=this.px(69,7.9); ctx.fillStyle=C.textSub; ctx.font='7px Segoe UI';
          ctx.textAlign='left'; ctx.textBaseline='middle';
          ctx.fillText('← 2.4M corridor →',p.px,p.py); }

        [ {x:68,w:4,l:'A-401'},{x:72,w:4,l:'A-402'},{x:76,w:4,l:'A-403'},
          {x:84,w:4,l:'A-404'},{x:88,w:4,l:'A-405'},{x:92,w:4,l:'A-406'},
          {x:96,w:4,l:'A-407'},{x:100,w:4,l:'A-408'},{x:104,w:4,l:'A-409'},
          {x:112,w:4,l:'A-410'},{x:116,w:4,l:'A-411'},{x:120,w:2,l:'A-412'} ].forEach(r=>{
            R(r.x,0,r.w,6,C.roomFill,C.roomBorder);
            T(r.x,0,r.w,6,r.l,'bold 7px Segoe UI');
        });
        R(80,0,4,6,C.openFill,C.roomBorder);  T(80,0,4,6,'open','6px Segoe UI',C.textSub);
        R(108,0,4,6,C.openFill,C.roomBorder); T(108,0,4,6,'open','6px Segoe UI',C.textSub);

        [ {x:68,w:6,l:'Design\nStudio',f:C.labFill,b:C.labBorder},
          {x:74,w:8,l:'AID\nLab',f:C.labFill,b:C.labBorder},
          {x:82,w:6,l:'A-415\nLab',f:C.labFill,b:C.labBorder},
          {x:88,w:8,l:'CI\nLab',f:C.labFill,b:C.labBorder},
          {x:98,w:8,l:'MIDAS\nLab',f:C.labFill,b:C.labBorder},
          {x:106,w:8,l:'A-417\nLab',f:C.labFill,b:C.labBorder},
          {x:114,w:6,l:'HMI\nLab',f:C.labFill,b:C.labBorder} ].forEach(r=>{
            R(r.x,10,r.w,7,r.f,r.b); T(r.x,10,r.w,7,r.l,'bold 7px Segoe UI');
        });

        R(74,17,8,5,C.discFill,C.discBorder); T(74,17,8,5,'Disc.\nRoom 1A','bold 7px Segoe UI','#c53030');
        R(98,17,8,5,C.discFill,C.discBorder); T(98,17,8,5,'Disc.\nRoom 2A','bold 7px Segoe UI','#c53030');

        { const p=this.px(95,0); ctx.fillStyle='#4a5568'; ctx.font='bold 9px Segoe UI';
          ctx.textAlign='center'; ctx.textBaseline='bottom';
          ctx.fillText('A - W I N G',p.px,p.py-3); }

        // Fire staircase markers
        [0,58,122].forEach(wx=>{
            const p=this.px(wx,22);
            ctx.fillStyle='#e53e3e'; ctx.font='bold 6px Segoe UI';
            ctx.textAlign='center'; ctx.textBaseline='top';
            ctx.fillText('▲FIRE STAIR',p.px,p.py+2);
        });

        // Floor title
        { const p=this.px(0,0); ctx.fillStyle=C.textSub; ctx.font='10px Segoe UI';
          ctx.textAlign='left'; ctx.textBaseline='bottom';
          ctx.fillText('4th Floor — R&D Building, IIIT Delhi  |  B-Wing + A-Wing',p.px,p.py-4); }
    }

    _drawEdges() {
        const ctx=this.ctx;
        ctx.strokeStyle=this.C.edgeLine; ctx.lineWidth=1.5;
        ctx.setLineDash([4,4]);
        this.edges.forEach(e=>{
            const a=this.nodes[e.from],b=this.nodes[e.to]; if(!a||!b)return;
            const pa=this.px(a.x,a.y),pb=this.px(b.x,b.y);
            ctx.beginPath(); ctx.moveTo(pa.px,pa.py); ctx.lineTo(pb.px,pb.py); ctx.stroke();
        });
        ctx.setLineDash([]);
    }

    _drawNodes() {
        const ctx=this.ctx;
        Object.entries(this.nodes).forEach(([id,n])=>{
            const p=this.px(n.x,n.y);
            const r=n.type==='room'?5:n.type==='landmark'?6:3;
            const fill=n.type==='room'?this.C.nodeRoom:n.type==='landmark'?this.C.nodeLmk:this.C.nodeCorr;
            ctx.beginPath(); ctx.arc(p.px,p.py,r,0,Math.PI*2);
            ctx.fillStyle=fill; ctx.fill();
            ctx.strokeStyle='white'; ctx.lineWidth=1; ctx.stroke();
            if(n.type==='room'||n.type==='landmark'){
                ctx.fillStyle=this.C.nodeLabel; ctx.font='7px Segoe UI';
                ctx.textAlign='center'; ctx.textBaseline='bottom';
                ctx.fillText(n.room_number||n.label,p.px,p.py-6);
            }
        });
    }

    _drawPath() {
        if(!this.navigationPath||this.navigationPath.length<2)return;
        const ctx=this.ctx,pts=this.navigationPath,s=this.px(pts[0].x,pts[0].y);
        const line=(w,c)=>{
            ctx.strokeStyle=c; ctx.lineWidth=w; ctx.lineCap=ctx.lineJoin='round';
            ctx.beginPath(); ctx.moveTo(s.px,s.py);
            pts.slice(1).forEach(p=>{const q=this.px(p.x,p.y);ctx.lineTo(q.px,q.py);});
            ctx.stroke();
        };
        line(14,this.C.pathGlow); line(4,this.C.pathLine);
        for(let i=0;i<pts.length-1;i++){
            const a=this.px(pts[i].x,pts[i].y),b=this.px(pts[i+1].x,pts[i+1].y);
            const ang=Math.atan2(b.py-a.py,b.px-a.px);
            ctx.save(); ctx.translate((a.px+b.px)/2,(a.py+b.py)/2); ctx.rotate(ang);
            ctx.fillStyle=this.C.pathLine; ctx.beginPath();
            ctx.moveTo(6,0); ctx.lineTo(-4,-4); ctx.lineTo(-4,4);
            ctx.closePath(); ctx.fill(); ctx.restore();
        }
    }

    _drawUser() {
        const ctx=this.ctx,p=this.px(this.userPosition.x,this.userPosition.y);
        ctx.beginPath(); ctx.arc(p.px,p.py,18,0,Math.PI*2); ctx.fillStyle=this.C.userGlow; ctx.fill();
        ctx.beginPath(); ctx.arc(p.px,p.py,8,0,Math.PI*2); ctx.fillStyle=this.C.userDot; ctx.fill();
        ctx.strokeStyle='white'; ctx.lineWidth=2; ctx.stroke();
    }

    _drawDest() {
        const node=this.nodes[this.destinationNode]; if(!node)return;
        const ctx=this.ctx,p=this.px(node.x,node.y);
        ctx.beginPath(); ctx.arc(p.px,p.py,16,0,Math.PI*2); ctx.fillStyle=this.C.destGlow; ctx.fill();
        ctx.beginPath(); ctx.arc(p.px,p.py,7,0,Math.PI*2); ctx.fillStyle=this.C.destPin; ctx.fill();
        ctx.strokeStyle='white'; ctx.lineWidth=2; ctx.stroke();
        ctx.fillStyle=this.C.destPin; ctx.font='bold 10px Segoe UI';
        ctx.textAlign='center'; ctx.textBaseline='bottom';
        ctx.fillText('📍 '+(node.label||''),p.px,p.py-14);
    }

    _drawScale() {
        const ctx=this.ctx,len=10*this.scale,x=this.canvas.width-len-20,y=this.canvas.height-16;
        ctx.strokeStyle='#4a5568'; ctx.lineWidth=2;
        ctx.beginPath();
        ctx.moveTo(x,y); ctx.lineTo(x+len,y);
        ctx.moveTo(x,y-4); ctx.lineTo(x,y+4);
        ctx.moveTo(x+len,y-4); ctx.lineTo(x+len,y+4);
        ctx.stroke();
        ctx.fillStyle='#4a5568'; ctx.font='9px Segoe UI';
        ctx.textAlign='center'; ctx.textBaseline='bottom';
        ctx.fillText('10 m',x+len/2,y-6);
    }

    _handleClick(e) {
        const rect=this.canvas.getBoundingClientRect();
        const sx=this.canvas.width/rect.width, sy=this.canvas.height/rect.height;
        const px=(e.clientX-rect.left)*sx, py=(e.clientY-rect.top)*sy;
        this.canvas.dispatchEvent(new CustomEvent('mapClick',{detail:this.world(px,py)}));
    }

    setUserPosition(x,y)          { this.userPosition={x,y}; this.render(); }
    setNavigationPath(pts,destId) { this.navigationPath=pts; this.destinationNode=destId; this.render(); }
    clearNavigation()              { this.navigationPath=null; this.destinationNode=null; this.render(); }
}
