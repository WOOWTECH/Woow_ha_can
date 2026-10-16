function t(t,e,i,r){var s,o=arguments.length,n=o<3?e:null===r?r=Object.getOwnPropertyDescriptor(e,i):r;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)n=Reflect.decorate(t,e,i,r);else for(var a=t.length-1;a>=0;a--)(s=t[a])&&(n=(o<3?s(n):o>3?s(e,i,n):s(e,i))||n);return o>3&&n&&Object.defineProperty(e,i,n),n}"function"==typeof SuppressedError&&SuppressedError;const e=globalThis,i=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,r=Symbol(),s=new WeakMap;let o=class{constructor(t,e,i){if(this._$cssResult$=!0,i!==r)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const e=this.t;if(i&&void 0===t){const i=void 0!==e&&1===e.length;i&&(t=s.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),i&&s.set(e,t))}return t}toString(){return this.cssText}};const n=(t,...e)=>{const i=1===t.length?t[0]:e.reduce((e,i,r)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+t[r+1],t[0]);return new o(i,t,r)},a=i?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const i of t.cssRules)e+=i.cssText;return(t=>new o("string"==typeof t?t:t+"",void 0,r))(e)})(t):t,{is:c,defineProperty:l,getOwnPropertyDescriptor:d,getOwnPropertyNames:h,getOwnPropertySymbols:p,getPrototypeOf:u}=Object,f=globalThis,m=f.trustedTypes,_=m?m.emptyScript:"",v=f.reactiveElementPolyfillSupport,g=(t,e)=>t,b={toAttribute(t,e){switch(e){case Boolean:t=t?_:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let i=t;switch(e){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t)}catch(t){i=null}}return i}},$=(t,e)=>!c(t,e),y={attribute:!0,type:String,converter:b,reflect:!1,useDefault:!1,hasChanged:$};Symbol.metadata??=Symbol("metadata"),f.litPropertyMetadata??=new WeakMap;let w=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=y){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const i=Symbol(),r=this.getPropertyDescriptor(t,i,e);void 0!==r&&l(this.prototype,t,r)}}static getPropertyDescriptor(t,e,i){const{get:r,set:s}=d(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:r,set(e){const o=r?.call(this);s?.call(this,e),this.requestUpdate(t,o,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??y}static _$Ei(){if(this.hasOwnProperty(g("elementProperties")))return;const t=u(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(g("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(g("properties"))){const t=this.properties,e=[...h(t),...p(t)];for(const i of e)this.createProperty(i,t[i])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,i]of e)this.elementProperties.set(t,i)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const i=this._$Eu(t,e);void 0!==i&&this._$Eh.set(i,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const i=new Set(t.flat(1/0).reverse());for(const t of i)e.unshift(a(t))}else void 0!==t&&e.push(a(t));return e}static _$Eu(t,e){const i=e.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((t,r)=>{if(i)t.adoptedStyleSheets=r.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const i of r){const r=document.createElement("style"),s=e.litNonce;void 0!==s&&r.setAttribute("nonce",s),r.textContent=i.cssText,t.appendChild(r)}})(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){const i=this.constructor.elementProperties.get(t),r=this.constructor._$Eu(t,i);if(void 0!==r&&!0===i.reflect){const s=(void 0!==i.converter?.toAttribute?i.converter:b).toAttribute(e,i.type);this._$Em=t,null==s?this.removeAttribute(r):this.setAttribute(r,s),this._$Em=null}}_$AK(t,e){const i=this.constructor,r=i._$Eh.get(t);if(void 0!==r&&this._$Em!==r){const t=i.getPropertyOptions(r),s="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:b;this._$Em=r;const o=s.fromAttribute(e,t.type);this[r]=o??this._$Ej?.get(r)??o,this._$Em=null}}requestUpdate(t,e,i,r=!1,s){if(void 0!==t){const o=this.constructor;if(!1===r&&(s=this[t]),i??=o.getPropertyOptions(t),!((i.hasChanged??$)(s,e)||i.useDefault&&i.reflect&&s===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,i))))return;this.C(t,e,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:r,wrapped:s},o){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),!0!==s||void 0!==o)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),!0===r&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,i]of t){const{wrapped:t}=i,r=this[e];!0!==t||this._$AL.has(e)||void 0===r||this.C(e,void 0,i,r)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};w.elementStyles=[],w.shadowRootOptions={mode:"open"},w[g("elementProperties")]=new Map,w[g("finalized")]=new Map,v?.({ReactiveElement:w}),(f.reactiveElementVersions??=[]).push("2.1.2");const x=globalThis,k=t=>t,A=x.trustedTypes,S=A?A.createPolicy("lit-html",{createHTML:t=>t}):void 0,E="$lit$",C=`lit$${Math.random().toFixed(9).slice(2)}$`,M="?"+C,N=`<${M}>`,P=document,D=()=>P.createComment(""),I=t=>null===t||"object"!=typeof t&&"function"!=typeof t,T=Array.isArray,O="[ \t\n\f\r]",R=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,U=/-->/g,z=/>/g,H=RegExp(`>|${O}(?:([^\\s"'>=/]+)(${O}*=${O}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),L=/'/g,F=/"/g,j=/^(?:script|style|textarea|title)$/i,B=t=>(e,...i)=>({_$litType$:t,strings:e,values:i}),W=B(1),q=B(2),V=Symbol.for("lit-noChange"),K=Symbol.for("lit-nothing"),J=new WeakMap,Z=P.createTreeWalker(P,129);function X(t,e){if(!T(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==S?S.createHTML(e):e}class Q{constructor({strings:t,_$litType$:e},i){let r;this.parts=[];let s=0,o=0;const n=t.length-1,a=this.parts,[c,l]=((t,e)=>{const i=t.length-1,r=[];let s,o=2===e?"<svg>":3===e?"<math>":"",n=R;for(let e=0;e<i;e++){const i=t[e];let a,c,l=-1,d=0;for(;d<i.length&&(n.lastIndex=d,c=n.exec(i),null!==c);)d=n.lastIndex,n===R?"!--"===c[1]?n=U:void 0!==c[1]?n=z:void 0!==c[2]?(j.test(c[2])&&(s=RegExp("</"+c[2],"g")),n=H):void 0!==c[3]&&(n=H):n===H?">"===c[0]?(n=s??R,l=-1):void 0===c[1]?l=-2:(l=n.lastIndex-c[2].length,a=c[1],n=void 0===c[3]?H:'"'===c[3]?F:L):n===F||n===L?n=H:n===U||n===z?n=R:(n=H,s=void 0);const h=n===H&&t[e+1].startsWith("/>")?" ":"";o+=n===R?i+N:l>=0?(r.push(a),i.slice(0,l)+E+i.slice(l)+C+h):i+C+(-2===l?e:h)}return[X(t,o+(t[i]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),r]})(t,e);if(this.el=Q.createElement(c,i),Z.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(r=Z.nextNode())&&a.length<n;){if(1===r.nodeType){if(r.hasAttributes())for(const t of r.getAttributeNames())if(t.endsWith(E)){const e=l[o++],i=r.getAttribute(t).split(C),n=/([.?@])?(.*)/.exec(e);a.push({type:1,index:s,name:n[2],strings:i,ctor:"."===n[1]?it:"?"===n[1]?rt:"@"===n[1]?st:et}),r.removeAttribute(t)}else t.startsWith(C)&&(a.push({type:6,index:s}),r.removeAttribute(t));if(j.test(r.tagName)){const t=r.textContent.split(C),e=t.length-1;if(e>0){r.textContent=A?A.emptyScript:"";for(let i=0;i<e;i++)r.append(t[i],D()),Z.nextNode(),a.push({type:2,index:++s});r.append(t[e],D())}}}else if(8===r.nodeType)if(r.data===M)a.push({type:2,index:s});else{let t=-1;for(;-1!==(t=r.data.indexOf(C,t+1));)a.push({type:7,index:s}),t+=C.length-1}s++}}static createElement(t,e){const i=P.createElement("template");return i.innerHTML=t,i}}function G(t,e,i=t,r){if(e===V)return e;let s=void 0!==r?i._$Co?.[r]:i._$Cl;const o=I(e)?void 0:e._$litDirective$;return s?.constructor!==o&&(s?._$AO?.(!1),void 0===o?s=void 0:(s=new o(t),s._$AT(t,i,r)),void 0!==r?(i._$Co??=[])[r]=s:i._$Cl=s),void 0!==s&&(e=G(t,s._$AS(t,e.values),s,r)),e}class Y{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:i}=this._$AD,r=(t?.creationScope??P).importNode(e,!0);Z.currentNode=r;let s=Z.nextNode(),o=0,n=0,a=i[0];for(;void 0!==a;){if(o===a.index){let e;2===a.type?e=new tt(s,s.nextSibling,this,t):1===a.type?e=new a.ctor(s,a.name,a.strings,this,t):6===a.type&&(e=new ot(s,this,t)),this._$AV.push(e),a=i[++n]}o!==a?.index&&(s=Z.nextNode(),o++)}return Z.currentNode=P,r}p(t){let e=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}}class tt{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,i,r){this.type=2,this._$AH=K,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=G(this,t,e),I(t)?t===K||null==t||""===t?(this._$AH!==K&&this._$AR(),this._$AH=K):t!==this._$AH&&t!==V&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>T(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==K&&I(this._$AH)?this._$AA.nextSibling.data=t:this.T(P.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:i}=t,r="number"==typeof i?this._$AC(t):(void 0===i.el&&(i.el=Q.createElement(X(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===r)this._$AH.p(e);else{const t=new Y(r,this),i=t.u(this.options);t.p(e),this.T(i),this._$AH=t}}_$AC(t){let e=J.get(t.strings);return void 0===e&&J.set(t.strings,e=new Q(t)),e}k(t){T(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let i,r=0;for(const s of t)r===e.length?e.push(i=new tt(this.O(D()),this.O(D()),this,this.options)):i=e[r],i._$AI(s),r++;r<e.length&&(this._$AR(i&&i._$AB.nextSibling,r),e.length=r)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=k(t).nextSibling;k(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class et{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,r,s){this.type=1,this._$AH=K,this._$AN=void 0,this.element=t,this.name=e,this._$AM=r,this.options=s,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=K}_$AI(t,e=this,i,r){const s=this.strings;let o=!1;if(void 0===s)t=G(this,t,e,0),o=!I(t)||t!==this._$AH&&t!==V,o&&(this._$AH=t);else{const r=t;let n,a;for(t=s[0],n=0;n<s.length-1;n++)a=G(this,r[i+n],e,n),a===V&&(a=this._$AH[n]),o||=!I(a)||a!==this._$AH[n],a===K?t=K:t!==K&&(t+=(a??"")+s[n+1]),this._$AH[n]=a}o&&!r&&this.j(t)}j(t){t===K?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class it extends et{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===K?void 0:t}}class rt extends et{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==K)}}class st extends et{constructor(t,e,i,r,s){super(t,e,i,r,s),this.type=5}_$AI(t,e=this){if((t=G(this,t,e,0)??K)===V)return;const i=this._$AH,r=t===K&&i!==K||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,s=t!==K&&(i===K||r);r&&this.element.removeEventListener(this.name,this,i),s&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class ot{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){G(this,t)}}const nt={I:tt},at=x.litHtmlPolyfillSupport;at?.(Q,tt),(x.litHtmlVersions??=[]).push("3.3.3");const ct=globalThis;let lt=class extends w{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,i)=>{const r=i?.renderBefore??e;let s=r._$litPart$;if(void 0===s){const t=i?.renderBefore??null;r._$litPart$=s=new tt(e.insertBefore(D(),t),t,void 0,i??{})}return s._$AI(t),s})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return V}};lt._$litElement$=!0,lt.finalized=!0,ct.litElementHydrateSupport?.({LitElement:lt});const dt=ct.litElementPolyfillSupport;dt?.({LitElement:lt}),(ct.litElementVersions??=[]).push("4.2.2");const ht={attribute:!0,type:String,converter:b,reflect:!1,hasChanged:$},pt=(t=ht,e,i)=>{const{kind:r,metadata:s}=i;let o=globalThis.litPropertyMetadata.get(s);if(void 0===o&&globalThis.litPropertyMetadata.set(s,o=new Map),"setter"===r&&((t=Object.create(t)).wrapped=!0),o.set(i.name,t),"accessor"===r){const{name:r}=i;return{set(i){const s=e.get.call(this);e.set.call(this,i),this.requestUpdate(r,s,t,!0,i)},init(e){return void 0!==e&&this.C(r,void 0,t,e),e}}}if("setter"===r){const{name:r}=i;return function(i){const s=this[r];e.call(this,i),this.requestUpdate(r,s,t,!0,i)}}throw Error("Unsupported decorator location: "+r)};function ut(t){return(e,i)=>"object"==typeof i?pt(t,e,i):((t,e,i)=>{const r=e.hasOwnProperty(i);return e.constructor.createProperty(i,t),r?Object.getOwnPropertyDescriptor(e,i):void 0})(t,e,i)}function ft(t){return ut({...t,state:!0,attribute:!1})}const mt=2**32;function _t(t){return Math.floor(t/2147483648)%2==1}function vt(t){const e=t%536870912;return _t(t)?e.toString(16).toUpperCase().padStart(8,"0"):(e%2048).toString(16).toUpperCase().padStart(3,"0")}function gt(t,e,i){if(16&e)return`${(536870912+t%536870912).toString(16).toUpperCase().padStart(8,"0")}#${i}`;const r=vt(t);return!function(t){return Math.floor(t/1073741824)%2==1}(t)||1&e?1&e?`${r}##${2&e?1:0}${i}`:`${r}#${i}`:`${r}#R`}class bt{constructor(t){this.exact=new Set,this.masks=[],this.ranges=[],this.error="";let e=!t.trim(),i="";for(const r of t.split(/[,;]/)){const t=r.trim();if(t)if("*"!==t)try{if(t.includes("-")){const[e,i]=t.split("-"),[r,s]=$t(e),[o,n]=$t(i);if(o<r)throw new Error(t);this.ranges.push([r,o,s||n])}else if(t.includes("/")){const[e,i]=t.split("/"),[r,s]=$t(e);this.masks.push([r,$t(i)[0],s])}else{const[e,i]=$t(t);this.exact.add(`${i?"x":""}${e}`)}}catch{i=t}else e=!0}this.all=e,this.error=i}matches(t){if(this.all)return!0;const e=_t(t),i=e?t%536870912:t%2048;if(this.exact.has(`${e?"x":""}${i}`))return!0;for(const[t,r,s]of this.masks)if(s===e&&(i&r)===(t&r))return!0;for(const[t,r,s]of this.ranges)if(s===e&&i>=t&&i<=r)return!0;return!1}}function $t(t){let e=t.trim();if(e.toLowerCase().startsWith("0x")&&(e=e.slice(2)),!/^[0-9a-fA-F]{1,8}$/.test(e))throw new Error(`bad CAN ID ${t}`);const i=parseInt(e,16);if(i>536870911)throw new Error(`CAN ID ${t} is out of range`);return[i,e.length>3||i>2047]}class yt{constructor(t){this.hass=t}subscribe(t){return this.hass().connection.subscribeMessage(t,{type:"woow_can/subscribe"})}snapshot(){return this.hass().callWS({type:"woow_can/snapshot"})}subscribeMonitor(t,e,i){return this.hass().connection.subscribeMessage(i,{type:"woow_can/monitor/subscribe",source:t,token:e})}ack(t,e){return this.hass().callWS({type:"woow_can/monitor/ack",token:t,seq:e})}clearMonitor(t){return this.hass().callWS({type:"woow_can/monitor/clear",source:t})}trace(t,e){return this.hass().callWS({type:"woow_can/trace",source:t,limit:e.limit??200,ids:e.ids??"",...null!=e.before?{before:e.before}:{},...e.direction?{direction:e.direction}:{}})}send(t,e,i=0,r=""){return this.hass().callWS({type:"woow_can/send",entry_id:t,frame:e,wait_ms:i,...r?{wait_id:r}:{}})}setEvents(t,e){return this.hass().callWS({type:"woow_can/interface/events",entry_id:t,event_filter:e})}savePeriodic(t){return this.hass().callWS({type:"woow_can/periodic/save",item:t})}controlPeriodic(t,e){return this.hass().callWS({type:"woow_can/periodic/control",item_id:t,action:e})}captures(){return this.hass().callWS({type:"woow_can/capture/list"})}capture(t,e){return this.hass().callWS({type:"woow_can/capture/control",action:t,...e})}async download(t){const e=await this.hass().callWS({type:"auth/sign_path",path:t,expires:60}),i=document.createElement("a");i.href=this.hass().hassUrl(e.path),i.download="",document.body.appendChild(i),i.click(),i.remove()}async upload(t){const e=await this.hass().fetchWithAuth(`/api/woow_can/captures?name=${encodeURIComponent(t.name)}`,{method:"POST",body:t});if(!e.ok)throw new Error(`${e.status} ${await e.text()}`);return(await e.json()).name}}function wt(t){return String(t&&"object"==typeof t&&"message"in t?t.message:t)}function xt(t,e){customElements.get(t)||customElements.define(t,e)}function kt(t,e){try{const i=window.localStorage.getItem(t);return i?JSON.parse(i):e}catch{return e}}function At(t,e){try{window.localStorage.setItem(t,JSON.stringify(e))}catch{}}const St={title:"WOOW CAN",tab_overview:"Overview",tab_monitor:"Monitor",tab_send:"Send",tab_capture:"Recordings",tab_activity:"Activity",loading:"Loading…",error:"Error: {msg}",cancel:"Cancel",close:"Close",save:"Save",delete:"Delete",edit:"Edit",add:"Add",start:"Start",stop:"Stop",none:"none",just_now:"just now",s_ago:"{n} s ago",m_ago:"{n} min ago",h_ago:"{n} h ago",d_ago:"{n} d ago",no_interfaces:"No CAN interfaces yet. Add one under Settings › Devices & services › WOOW CAN; without hardware, add a virtual interface to try things out.",state_error_active:"Normal",state_error_warning:"Error warning",state_error_passive:"Error passive",state_bus_off:"Bus off",state_stopped:"Stopped",state_sleeping:"Sleeping",state_virtual:"Virtual",state_unknown:"Unknown",unavailable:"Unavailable",listen_only:"listen only",can_fd:"CAN FD",kbps:"{n} kbit/s",virtual_iface:"virtual",load:"Bus load",load_values:"now {now} · peak {peak} · 1/5/15 min {a1} / {a5} / {a15}",load_hint:"Estimated with worst-case bit stuffing; it can exceed 100 %.",rates:"received {rx}/s · sent {tx}/s",traffic:"Traffic",seen:"Seen since start",tec_rec:"TEC / REC",controller_events:"Warnings / passive / bus-off / restarts",bus_errors:"Bus errors",arbitration_lost:"Arbitration lost",not_supported:"not reported by this controller",reporting_off:"reporting off",drops:"Dropped (socket / controller overflow / over the event rate)",last_error:"Last error frame",ids_seen:"{n} IDs · {f} frames",recording_now:"Recording {name} ({n} frames)",clock_mhz:"clock {n} MHz",sample_point:"sample point {n} %",events_filter:"Events for: {x}",events_none:"No events (event filter empty)",open_monitor:"Monitor",hint_passive:"Nothing on the bus acknowledges this interface's frames. Check the wiring, the 120 Ω termination at both ends and that every node uses the same bitrate.",hint_bus_off_auto:"The controller went bus-off; it restarts after {ms} ms.",hint_bus_off_manual:"The controller went bus-off and stays off: reload the interface.",hint_listen_only:"Listen only: this interface never acknowledges or sends.",hint_overflow:"The controller lost {n} frames (receive overflow): the bus is busier than it can follow.",hint_socket_drops:"{n} frames were dropped before Home Assistant read them.",sparkline:"Load over the last minutes","err_controller:rx_overflow":"receive overflow","err_controller:tx_overflow":"transmit overflow","err_controller:rx_warning":"receive errors at warning level","err_controller:tx_warning":"transmit errors at warning level","err_controller:rx_passive":"receive error passive","err_controller:tx_passive":"transmit error passive","err_controller:active":"back to error active",err_controller:"controller problem","err_protocol:bit":"bit error","err_protocol:form":"form error","err_protocol:stuff":"stuff error","err_protocol:bit0":"could not send a dominant bit","err_protocol:bit1":"could not send a recessive bit","err_protocol:overload":"bus overload","err_protocol:active_error":"active error flag","err_protocol:on_tx":"while transmitting",err_protocol:"protocol error",err_tx_timeout:"transmit timeout",err_lost_arbitration:"lost arbitration",err_transceiver:"transceiver problem",err_no_ack:"no acknowledgement",err_bus_off:"bus off",err_bus_error:"bus error",err_restarted:"controller restarted",source:"Source",file_source:"{name} (file)",pause:"Pause",resume:"Resume",clear:"Clear",notch:"Notch",notch_clear:"Clear notch",changing_only:"Changing only",hide_inactive:"Hide silent > 5 s",view_hex:"HEX",view_bin:"Binary",filter_ph:"IDs: 123, 7E0/7F0, 100-1FF",filter_bad:"Not understood: {x}",col_id:"ID",col_name:"Name",col_len:"Len",col_data:"Data",col_count:"Count",col_hz:"Hz",col_period:"Period",col_dchg:"Change gap",col_age:"Age",col_time:"Time",col_dir:"Dir",dir_rx:"Rx",dir_tx:"Tx",dir_local:"this host",monitor_empty:"No frames yet. Check that the bus is connected and every node uses the same bitrate, or open a recording under Recordings.",monitor_hint:"One row per ID. A changed byte lights up and fades: cyan rising, red falling, grey-violet for bytes that keep jumping (counters, checksums). To find a signal: leave the equipment alone for 10 s, press Notch two or three times until the screen is quiet, then operate the equipment and watch which bytes light up.",notch_added:"Masked {n} bits that changed in the last 2 s.",notch_none:"No bits changed in the last 2 s.",overflow:"More than 4096 IDs: {n} further frames are only counted.",frames_total:"{ids} IDs · {n} frames",row_pin:"Pin",row_unpin:"Unpin",row_send:"Send again",row_events:"Fire events",row_events_on:"Fires events",row_trace:"In time order",row_notch:"Notch this row",detail_period:"Period {avg} ms ({min}–{max})",detail_rate:"{hz} frames/s",detail_changed:"Data last changed {ago}; gap between the last two changes {gap}",paused_title:"Paused: frames in time order, newest first",trace_older:"Older",trace_start:"That is the oldest frame in the buffer.",trace_all_dirs:"Both directions",trace_time:"Time",trace_delta:"Δ",trace_error:"error frame: {x}",trace_empty:"No frames match.",events_added:"Frames with ID {id} now fire woow_can_frame events.",gone:"The interface was reloaded; reconnecting…",offline_note:"Recording {file}: {n} frames. The monitor shows the state at the end of the file.",send_title:"Send a frame",interface:"Interface",frame:"Frame",frame_ph:"123#11223344",frame_help:"ID#data: 1–3 digit IDs are 11-bit, longer ones 29-bit; 123#R is a remote frame; ID##1data is CAN FD (1 = bit rate switch).",wait_id:"Reply ID",wait_ms:"Wait (ms)",send:"Send",sent_ok:"Sent {frame}",reply:"Reply {frame}",no_reply:"No reply (timed out)",cannot_send:"{name} cannot send: {why}",why_listen:"it is set to listen only (turn that off in the interface settings)",why_unavailable:"it is not available",confirm_title:"First send on {name}",confirm_text:"Every node on the bus receives this frame. On a vehicle, machine or battery bus, only send frames whose effect you know.",confirm_ok:"Send",periodic_title:"Periodic sends",periodic_hint:"Frames sent every N ms. After Home Assistant restarts every item is stopped.",name:"Name",period_ms:"Period (ms)",count:"Count (0 = no limit)",running:"running",stopped:"stopped",sent_n:"{n} sent",stopped_by_count:"count reached",stopped_by_error:"stopped: {x}",stopped_by_interface:"interface stopped",periodic_empty:"No periodic sends yet.",capture_title:"Record",capture_hint:"Record an interface to a candump log file (canplayer, SavvyCAN, python-can and Wireshark read it), kept in Home Assistant's config folder under woow_can/captures.",record:"Record",stop_record:"Stop",recording:"Recording · {n} frames · {size}",export:"Download buffer",export_hint:"The last {n} frames held in memory, as a candump log.",files_title:"Recordings",files_empty:"No recordings yet.",download:"Download",open:"Open",upload:"Upload a log file",uploaded:"Uploaded {name}.",opened:"Opened; pick it as the source on the Monitor tab.",offline_title:"Open files",truncated:"only the last {n} frames",delete_confirm:"Delete {name}?",all_channels:"All sources",channel_service:"Service / AI",channel_panel:"Panel",channel_entity:"Entity",activity_hint:"Sends and changes made by AI agents (through services) and by people (in this panel).",activity_empty:"Nothing yet.",quoted:"“{x}”",log_sent:"sent {frame} on {port}",log_send_failed:"sending {frame} on {port} failed: {error}",log_periodic_saved:"saved periodic send “{name}”: {frame} every {period} ms on {port}",log_periodic_deleted:"deleted periodic send “{name}”",log_periodic_started:"started periodic send “{name}” on {port}",log_periodic_stopped:"stopped periodic send “{name}” ({sent} sent)",log_periodic_failed:"periodic send “{name}” stopped: {error}",log_capture_started:"started recording {file} on {port}",log_capture_stopped:"stopped recording {file} ({frames} frames)",log_capture_deleted:"deleted recording {file}",log_capture_uploaded:"uploaded {file}",log_monitor_cleared:"cleared the monitor of {port}"},Et={title:"WOOW CAN",tab_overview:"總覽",tab_monitor:"監看",tab_send:"發送",tab_capture:"擷取",tab_activity:"活動",loading:"載入中…",error:"錯誤：{msg}",cancel:"取消",close:"關閉",save:"儲存",delete:"刪除",edit:"編輯",add:"新增",start:"開始",stop:"停止",none:"無",just_now:"剛剛",s_ago:"{n} 秒前",m_ago:"{n} 分鐘前",h_ago:"{n} 小時前",d_ago:"{n} 天前",no_interfaces:"還沒有 CAN 介面。請到「設定 › 裝置與服務 › WOOW CAN」新增；沒有硬體的話，可以新增虛擬介面先試用。",state_error_active:"正常",state_error_warning:"錯誤警告",state_error_passive:"錯誤被動",state_bus_off:"Bus off（已離線）",state_stopped:"已停止",state_sleeping:"休眠",state_virtual:"虛擬介面",state_unknown:"未知",unavailable:"無法使用",listen_only:"只監聽",can_fd:"CAN FD",kbps:"{n} kbit/s",virtual_iface:"虛擬",load:"匯流排負載",load_values:"目前 {now} · 峰值 {peak} · 1／5／15 分鐘 {a1}／{a5}／{a15}",load_hint:"以最壞位元填充估算，所以可能超過 100%。",rates:"收 {rx} 筆/秒 · 送 {tx} 筆/秒",traffic:"流量",seen:"啟動以來",tec_rec:"TEC／REC",controller_events:"錯誤警告／錯誤被動／Bus off／重啟",bus_errors:"匯流排錯誤",arbitration_lost:"仲裁失敗",not_supported:"這顆控制器不回報",reporting_off:"未開啟回報",drops:"丟包（socket／控制器溢位／超過事件速率）",last_error:"最後一筆錯誤訊框",ids_seen:"{n} 個 ID · {f} 筆",recording_now:"錄製中：{name}（{n} 筆）",clock_mhz:"時脈 {n} MHz",sample_point:"取樣點 {n}%",events_filter:"觸發事件：{x}",events_none:"不觸發事件（事件 ID 空白）",open_monitor:"監看",hint_passive:"送出的訊框沒有任何節點回應確認（ACK）。請檢查接線、兩端的 120 Ω 終端電阻，以及所有節點的速率是否一致。",hint_bus_off_auto:"控制器進入 bus off，{ms} ms 後會自動重啟。",hint_bus_off_manual:"控制器進入 bus off，不會自動恢復：請重新載入這個介面。",hint_listen_only:"只監聽：這個介面不回 ACK，也不能發送。",hint_overflow:"控制器漏收了 {n} 筆（接收溢位）：匯流排比它能處理的還忙。",hint_socket_drops:"有 {n} 筆在 Home Assistant 讀取前就被丟掉了。",sparkline:"最近幾分鐘的負載","err_controller:rx_overflow":"接收溢位","err_controller:tx_overflow":"發送溢位","err_controller:rx_warning":"接收錯誤達警告","err_controller:tx_warning":"發送錯誤達警告","err_controller:rx_passive":"接收錯誤被動","err_controller:tx_passive":"發送錯誤被動","err_controller:active":"恢復正常",err_controller:"控制器問題","err_protocol:bit":"位元錯誤","err_protocol:form":"格式錯誤","err_protocol:stuff":"填充錯誤","err_protocol:bit0":"送不出顯性位元","err_protocol:bit1":"送不出隱性位元","err_protocol:overload":"匯流排過載","err_protocol:active_error":"主動錯誤旗標","err_protocol:on_tx":"發送時發生",err_protocol:"協定錯誤",err_tx_timeout:"發送逾時",err_lost_arbitration:"仲裁失敗",err_transceiver:"收發器問題",err_no_ack:"沒有人回 ACK",err_bus_off:"Bus off",err_bus_error:"匯流排錯誤",err_restarted:"控制器已重啟",source:"來源",file_source:"{name}（檔案）",pause:"暫停",resume:"繼續",clear:"清除",notch:"Notch",notch_clear:"清除 Notch",changing_only:"只看在變",hide_inactive:"隱藏 5 秒沒收到的",view_hex:"HEX",view_bin:"二進位",filter_ph:"篩選 ID：123, 7E0/7F0, 100-1FF",filter_bad:"看不懂：{x}",col_id:"ID",col_name:"名稱",col_len:"長度",col_data:"資料",col_count:"次數",col_hz:"Hz",col_period:"週期",col_dchg:"變化間隔",col_age:"距今",col_time:"時間",col_dir:"方向",dir_rx:"收",dir_tx:"送",dir_local:"本機",monitor_empty:"還沒收到任何訊框。請確認匯流排有接上、所有節點速率一致；或到「擷取」分頁開啟一個紀錄檔。",monitor_hint:"每個 ID 一列。數值變了會上色再慢慢淡掉：上升青、下降紅，一直在跳的（計數器、校驗碼）用灰紫。找訊號的方法：先不要操作 10 秒，按 Notch 兩三次直到畫面安靜，再操作設備，看哪幾格亮起來。",notch_added:"已遮掉 {n} 個最近 2 秒內變過的位元。",notch_none:"最近 2 秒沒有位元變動。",overflow:"ID 超過 4096 個，另外 {n} 筆只計數。",frames_total:"{ids} 個 ID · 共 {n} 筆",row_pin:"釘選",row_unpin:"取消釘選",row_send:"再送一次",row_events:"觸發事件",row_events_on:"已觸發事件",row_trace:"看時間序",row_notch:"遮掉這列",detail_period:"週期 {avg} ms（{min}–{max}）",detail_rate:"每秒 {hz} 筆",detail_changed:"資料最後變化：{ago}；最近兩次變化間隔 {gap}",paused_title:"已暫停：依時間排列（新的在前）",trace_older:"更早",trace_start:"已經是緩衝區裡最舊的一筆。",trace_all_dirs:"收送都看",trace_time:"時間",trace_delta:"間隔",trace_error:"錯誤訊框：{x}",trace_empty:"沒有符合的訊框。",events_added:"ID {id} 收到時，會觸發 woow_can_frame 事件。",gone:"介面重新載入了，正在重新連線…",offline_note:"紀錄檔 {file}：{n} 筆。監看顯示的是檔案結尾時的狀態。",send_title:"發送訊框",interface:"介面",frame:"訊框",frame_ph:"123#11223344",frame_help:"寫法：ID#資料。1–3 位數的 ID＝11-bit，更長＝29-bit；123#R＝遠端訊框；ID##1資料＝CAN FD（1＝切換速率）。",wait_id:"等回覆 ID",wait_ms:"等待（ms）",send:"送出",sent_ok:"已送出 {frame}",reply:"回覆 {frame}",no_reply:"沒有回覆（逾時）",cannot_send:"{name} 不能發送：{why}",why_listen:"設定為只監聽（到介面設定關閉）",why_unavailable:"目前無法使用",confirm_title:"第一次從 {name} 發送",confirm_text:"匯流排上的所有節點都會收到這筆訊框。如果是車輛、機器或電池的匯流排，請只送你清楚作用的訊框。",confirm_ok:"確定送出",periodic_title:"週期發送",periodic_hint:"每隔 N ms 送一次。Home Assistant 重新啟動後，所有項目都會先停止。",name:"名稱",period_ms:"週期（ms）",count:"次數（0＝不限）",running:"執行中",stopped:"已停止",sent_n:"已送 {n} 筆",stopped_by_count:"已送滿次數",stopped_by_error:"出錯停止：{x}",stopped_by_interface:"介面停止",periodic_empty:"還沒有週期發送。",capture_title:"錄製",capture_hint:"把介面的訊框錄成 candump 紀錄檔（canplayer、SavvyCAN、python-can、Wireshark 都能讀），存在 Home Assistant 設定資料夾的 woow_can/captures。",record:"開始錄製",stop_record:"停止",recording:"錄製中 · {n} 筆 · {size}",export:"下載緩衝區",export_hint:"記憶體裡最近的 {n} 筆，存成 candump 紀錄檔。",files_title:"擷取檔",files_empty:"還沒有擷取檔。",download:"下載",open:"開啟",upload:"上傳紀錄檔",uploaded:"已上傳 {name}。",opened:"已開啟；到「監看」分頁把來源切到這個檔案。",offline_title:"已開啟的檔案",truncated:"只載入最後 {n} 筆",delete_confirm:"刪除 {name}？",all_channels:"全部來源",channel_service:"服務／AI",channel_panel:"面板",channel_entity:"實體",activity_hint:"AI（透過服務）和人（在這個面板）做的發送與變更，都記在這裡。",activity_empty:"還沒有紀錄。",quoted:"「{x}」",log_sent:"從 {port} 送出 {frame}",log_send_failed:"從 {port} 送出 {frame} 失敗：{error}",log_periodic_saved:"儲存週期發送「{name}」：{frame}，每 {period} ms，{port}",log_periodic_deleted:"刪除週期發送「{name}」",log_periodic_started:"開始週期發送「{name}」（{port}）",log_periodic_stopped:"停止週期發送「{name}」（已送 {sent} 筆）",log_periodic_failed:"週期發送「{name}」出錯停止：{error}",log_capture_started:"開始錄製 {file}（{port}）",log_capture_stopped:"停止錄製 {file}（{frames} 筆）",log_capture_deleted:"刪除擷取檔 {file}",log_capture_uploaded:"上傳擷取檔 {file}",log_monitor_cleared:"清除 {port} 的監看"};function Ct(t){const e=t.toLowerCase().startsWith("zh")?Et:St;return(t,i)=>{let r=e[t]??St[t]??t;if(i)for(const[t,e]of Object.entries(i))r=r.split(`{${t}}`).join(String(e));return r}}function Mt(t){return t in St}function Nt(t,e,i=Date.now()/1e3){const r=Math.max(0,i-t);return r<5?e("just_now"):r<60?e("s_ago",{n:Math.floor(r)}):r<3600?e("m_ago",{n:Math.floor(r/60)}):r<86400?e("h_ago",{n:Math.floor(r/3600)}):e("d_ago",{n:Math.floor(r/86400)})}function Pt(t){const e=new Date(1e3*t),i=(t,e=2)=>String(t).padStart(e,"0");return`${i(e.getHours())}:${i(e.getMinutes())}:${i(e.getSeconds())}.${i(e.getMilliseconds(),3)}`}function Dt(t){return null!=t&&isFinite(t)?t<1?`${(1e3*t).toFixed(t<.01?2:1)} ms`:t<100?`${t.toFixed(2)} s`:`${Math.round(t)} s`:"–"}function It(t){return t<1024?`${t} B`:t<1048576?`${(t/1024).toFixed(1)} KB`:`${(t/1024/1024).toFixed(1)} MB`}function Tt(t){return null==t?"–":`${t.toFixed(t<10?1:0)}%`}const Ot=n`
  :host {
    display: block;
    color: var(--primary-text-color);
    font-family: var(--paper-font-body1_-_font-family, Roboto, "Noto Sans TC", sans-serif);
  }
  .card {
    background: var(--card-background-color, #fff);
    border: 1px solid var(--divider-color, #e0e0e0);
    border-radius: var(--ha-card-border-radius, 12px);
    padding: 16px;
    margin-bottom: 16px;
  }
  .card h2 {
    margin: 0 0 12px;
    font-size: 1.1em;
    font-weight: 500;
  }
  .row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }
  .grow {
    flex: 1 1 auto;
    min-width: 0;
  }
  .muted {
    color: var(--secondary-text-color);
    font-size: 0.9em;
  }
  .mono {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 0.92em;
    word-break: break-all;
  }
  .chip {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 10px;
    font-size: 0.8em;
    line-height: 1.6;
    background: var(--secondary-background-color, #eee);
    color: var(--secondary-text-color);
    white-space: nowrap;
  }
  .chip.ok {
    background: rgba(67, 160, 71, 0.15);
    color: var(--success-color, #43a047);
  }
  .chip.warn {
    background: rgba(255, 152, 0, 0.15);
    color: var(--warning-color, #ff9800);
  }
  .chip.bad {
    background: rgba(219, 68, 55, 0.12);
    color: var(--error-color, #db4437);
  }
  .chip.info {
    background: rgba(3, 169, 244, 0.14);
    color: var(--info-color, #039be5);
  }
  button {
    font: inherit;
    border: 1px solid var(--divider-color, #ccc);
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color);
    border-radius: 8px;
    padding: 4px 10px;
    cursor: pointer;
  }
  button:hover {
    border-color: var(--primary-color);
  }
  button.primary {
    background: var(--primary-color);
    border-color: var(--primary-color);
    color: var(--text-primary-color, #fff);
  }
  button.link {
    border: none;
    background: none;
    color: var(--primary-color);
    padding: 2px 4px;
  }
  button.danger {
    color: var(--error-color, #db4437);
  }
  button:disabled {
    opacity: 0.5;
    cursor: default;
  }
  input,
  select {
    font: inherit;
    color: var(--primary-text-color);
    background: var(--card-background-color, #fff);
    border: 1px solid var(--divider-color, #ccc);
    border-radius: 8px;
    padding: 6px 8px;
    min-width: 0;
  }
  input:focus,
  select:focus {
    outline: 2px solid var(--primary-color);
    outline-offset: -1px;
  }
  .empty {
    padding: 24px 8px;
    text-align: center;
    color: var(--secondary-text-color);
  }
  .rx {
    color: var(--success-color, #43a047);
  }
  .tx {
    color: var(--info-color, #039be5);
  }
`,Rt=n`
  .bytes {
    display: flex;
    gap: 2px;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-variant-numeric: tabular-nums;
  }
  .byte {
    min-width: 2.3em;
    text-align: center;
    border-radius: 4px;
    padding: 0 1px;
    line-height: 1.6;
  }
  .byte.bin {
    min-width: 5.6em;
    letter-spacing: 0.02em;
  }
  .byte.notched {
    box-shadow: inset 0 -2px 0 var(--secondary-text-color);
  }
`;class Ut extends lt{constructor(){super(...arguments),this.entries=[],this.now=0,this.channel=""}channelLabel(t){const e=`channel_${t}`;return Mt(e)?this.t(e):t}message(t){const e=`log_${t.msg}`;return t.msg&&Mt(e)?this.t(e,{...t.args??{}}):t.summary}render(){const t=this.t,e=this.entries.filter(t=>!this.channel||t.channel===this.channel).sort((t,e)=>e.t-t.t);return W`<div class="card">
      <div class="row">
        <h2 class="grow">${t("tab_activity")}</h2>
        <select @change=${t=>this.channel=(t=>t.target.value)(t)}>
          <option value="">${t("all_channels")}</option>
          ${["service","panel","entity"].map(t=>W`<option value=${t}>${this.channelLabel(t)}</option>`)}
        </select>
      </div>
      <div class="muted">${t("activity_hint")}</div>
      ${0===e.length?W`<div class="empty">${t("activity_empty")}</div>`:e.map(e=>W`<div class="entry">
              <div class="when" title=${new Date(1e3*e.t).toLocaleString()}>${Nt(e.t,t)}<br />${Pt(e.t).slice(0,8)}</div>
              <div>
                <div class="row">
                  <span class="chip ${"service"===e.channel?"info":""}">${this.channelLabel(e.channel)}</span>
                  ${e.user?W`<span class="chip">${e.user}</span>`:K}
                  ${e.port_id?W`<span class="muted">${this.portName(e.port_id)}</span>`:K}
                </div>
                <div class=${e.ok?"":"fail"} title=${e.summary}>${e.ok?"":"✗ "}${this.message(e)}</div>
                ${e.note?W`<div class="note">${t("quoted",{x:e.note})}</div>`:K}
              </div>
            </div>`)}
    </div>`}}Ut.styles=[Ot,n`
      .entry {
        display: grid;
        grid-template-columns: 7.5em 1fr;
        gap: 4px 12px;
        padding: 10px 0;
        border-top: 1px solid var(--divider-color, #eee);
      }
      .when {
        color: var(--secondary-text-color);
        font-size: 0.85em;
      }
      .note {
        font-style: italic;
        color: var(--secondary-text-color);
      }
      .fail {
        color: var(--error-color, #db4437);
      }
    `],t([ut({attribute:!1})],Ut.prototype,"entries",void 0),t([ut({attribute:!1})],Ut.prototype,"now",void 0),t([ut({attribute:!1})],Ut.prototype,"t",void 0),t([ut({attribute:!1})],Ut.prototype,"portName",void 0),t([ft()],Ut.prototype,"channel",void 0),xt("woow-can-activity",Ut);class zt extends lt{constructor(){super(...arguments),this.interfaces=[],this.offline=[],this.files=[],this.message=null,this.deleting="",this.busy=!1}async run(t,e){this.busy=!0;try{await t(),this.message=e?{ok:!0,text:e}:null}catch(t){this.message={ok:!1,text:this.t("error",{msg:wt(t)})}}finally{this.busy=!1}}changed(){this.dispatchEvent(new CustomEvent("captures-changed"))}async upload(t){const e=t.target,i=e.files?.[0];e.value="",i&&await this.run(async()=>{const t=await this.api.upload(i);this.message={ok:!0,text:this.t("uploaded",{name:t})},this.changed()})}async open(t){await this.run(async()=>{const e=await this.api.capture("open",{name:t}),i=e.sources?.[0];i&&this.dispatchEvent(new CustomEvent("open-source",{detail:i.id}))},this.t("opened"))}render(){const t=this.t;return W`<div class="card">
        <h2>${t("capture_title")}</h2>
        <div class="muted">${t("capture_hint")}</div>
        <div class="ifaces" style="margin-top:12px">
          ${this.interfaces.map(e=>W`<div class="row">
            <b>${e.name}</b><span class="muted">${e.port}</span>
            <span class="grow"></span>
            ${e.recording?W`<span class="chip bad">● ${t("recording",{n:e.recording.frames.toLocaleString(),size:It(e.recording.bytes)})}</span>
                  <button ?disabled=${this.busy} @click=${()=>this.run(async()=>{await this.api.capture("stop",{entry_id:e.id}),this.changed()})}>${t("stop_record")}</button>`:W`<button class="primary" ?disabled=${this.busy} @click=${()=>this.run(async()=>{await this.api.capture("start",{entry_id:e.id}),this.changed()})}>${t("record")}</button>`}
            <button title=${t("export_hint",{n:(e.trace.end-e.trace.first).toLocaleString()})}
              @click=${()=>this.run(()=>this.api.download(`/api/woow_can/export/${e.id}`))}>${t("export")}</button>
          </div>`)}
        </div>
        ${this.message?W`<div class="chip ${this.message.ok?"ok":"bad"}" style="margin-top:10px;white-space:normal">${this.message.text}</div>`:K}
      </div>
      <div class="card">
        <div class="row">
          <h2 class="grow">${t("files_title")}</h2>
          <label><button @click=${()=>this.renderRoot.querySelector("#upload")?.click()}>
            ${t("upload")}</button></label>
          <input id="upload" type="file" accept=".log,.txt" @change=${this.upload} />
        </div>
        ${0===this.files.length?W`<div class="empty">${t("files_empty")}</div>`:W`<div class="wrap"><table>
              <tbody>
                ${this.files.map(e=>W`<tr>
                  <td class="mono">${e.recording?W`<span class="chip bad">●</span> `:K}${e.name}</td>
                  <td class="num">${It(e.size)}</td>
                  <td class="muted">${Nt(e.modified,t)}</td>
                  <td class="row">
                    <button class="link" @click=${()=>this.run(()=>this.api.download(`/api/woow_can/captures/${encodeURIComponent(e.name)}`))}>${t("download")}</button>
                    <button class="link" ?disabled=${e.recording} @click=${()=>this.open(e.name)}>${t("open")}</button>
                    ${this.deleting===e.name?W`<span>${t("delete_confirm",{name:e.name})}</span>
                          <button class="danger" @click=${()=>this.run(async()=>{this.deleting="",await this.api.capture("delete",{name:e.name}),this.changed()})}>${t("delete")}</button>
                          <button @click=${()=>this.deleting=""}>${t("cancel")}</button>`:W`<button class="link danger" ?disabled=${e.recording} @click=${()=>this.deleting=e.name}>
                          ${t("delete")}</button>`}
                  </td>
                </tr>`)}
              </tbody>
            </table></div>`}
        ${this.offline.length?W`<h2 style="margin-top:16px">${t("offline_title")}</h2>
              ${this.offline.map(e=>W`<div class="row">
                <span class="mono grow">${e.name}</span>
                <span class="muted">${e.frames.toLocaleString()}${e.truncated?` · ${t("truncated",{n:e.frames})}`:""}</span>
                <button class="link" @click=${()=>this.dispatchEvent(new CustomEvent("open-source",{detail:e.id}))}>
                  ${t("tab_monitor")}</button>
                <button class="link" @click=${()=>this.run(()=>this.api.capture("close",{source:e.id}))}>${t("close")}</button>
              </div>`)}`:K}
      </div>`}}zt.styles=[Ot,n`
      .ifaces {
        display: grid;
        gap: 10px;
      }
      .wrap {
        overflow-x: auto;
      }
      table {
        border-collapse: collapse;
        width: 100%;
      }
      th,
      td {
        text-align: left;
        padding: 6px 8px;
        border-bottom: 1px solid var(--divider-color, #eee);
        white-space: nowrap;
      }
      th {
        color: var(--secondary-text-color);
        font-weight: 500;
        font-size: 0.9em;
      }
      td.num {
        text-align: right;
        font-variant-numeric: tabular-nums;
      }
      input[type="file"] {
        display: none;
      }
    `],t([ut({attribute:!1})],zt.prototype,"interfaces",void 0),t([ut({attribute:!1})],zt.prototype,"offline",void 0),t([ut({attribute:!1})],zt.prototype,"files",void 0),t([ut({attribute:!1})],zt.prototype,"t",void 0),t([ut({attribute:!1})],zt.prototype,"api",void 0),t([ft()],zt.prototype,"message",void 0),t([ft()],zt.prototype,"deleting",void 0),t([ft()],zt.prototype,"busy",void 0),xt("woow-can-capture",zt);const Ht=2;let Lt=class{constructor(t){}get _$AU(){return this._$AM._$AU}_$AT(t,e,i){this._$Ct=t,this._$AM=e,this._$Ci=i}_$AS(t,e){return this.update(t,e)}update(t,e){return this.render(...e)}};const{I:Ft}=nt,jt=t=>t,Bt=()=>document.createComment(""),Wt=(t,e,i)=>{const r=t._$AA.parentNode,s=void 0===e?t._$AB:e._$AA;if(void 0===i){const e=r.insertBefore(Bt(),s),o=r.insertBefore(Bt(),s);i=new Ft(e,o,t,t.options)}else{const e=i._$AB.nextSibling,o=i._$AM,n=o!==t;if(n){let e;i._$AQ?.(t),i._$AM=t,void 0!==i._$AP&&(e=t._$AU)!==o._$AU&&i._$AP(e)}if(e!==s||n){let t=i._$AA;for(;t!==e;){const e=jt(t).nextSibling;jt(r).insertBefore(t,s),t=e}}}return i},qt=(t,e,i=t)=>(t._$AI(e,i),t),Vt={},Kt=(t,e=Vt)=>t._$AH=e,Jt=t=>{t._$AR(),t._$AA.remove()},Zt=(t,e,i)=>{const r=new Map;for(let s=e;s<=i;s++)r.set(t[s],s);return r},Xt=(t=>(...e)=>({_$litDirective$:t,values:e}))(class extends Lt{constructor(t){if(super(t),t.type!==Ht)throw Error("repeat() can only be used in text expressions")}dt(t,e,i){let r;void 0===i?i=e:void 0!==e&&(r=e);const s=[],o=[];let n=0;for(const e of t)s[n]=r?r(e,n):n,o[n]=i(e,n),n++;return{values:o,keys:s}}render(t,e,i){return this.dt(t,e,i).values}update(t,[e,i,r]){const s=(t=>t._$AH)(t),{values:o,keys:n}=this.dt(e,i,r);if(!Array.isArray(s))return this.ut=n,o;const a=this.ut??=[],c=[];let l,d,h=0,p=s.length-1,u=0,f=o.length-1;for(;h<=p&&u<=f;)if(null===s[h])h++;else if(null===s[p])p--;else if(a[h]===n[u])c[u]=qt(s[h],o[u]),h++,u++;else if(a[p]===n[f])c[f]=qt(s[p],o[f]),p--,f--;else if(a[h]===n[f])c[f]=qt(s[h],o[f]),Wt(t,c[f+1],s[h]),h++,f--;else if(a[p]===n[u])c[u]=qt(s[p],o[u]),Wt(t,s[h],s[p]),p--,u++;else if(void 0===l&&(l=Zt(n,u,f),d=Zt(a,h,p)),l.has(a[h]))if(l.has(a[p])){const e=d.get(n[u]),i=void 0!==e?s[e]:null;if(null===i){const e=Wt(t,s[h]);qt(e,o[u]),c[u]=e}else c[u]=qt(i,o[u]),Wt(t,s[h],i),s[e]=null;u++}else Jt(s[p]),p--;else Jt(s[h]),h++;for(;u<=f;){const e=Wt(t,c[f+1]);qt(e,o[u]),c[u++]=e}for(;h<=p;){const t=s[h++];null!==t&&Jt(t)}return this.ut=n,Kt(t,c),V}}),Qt=2e3,Gt={rise:"#00bbff",fall:"#ff3b30",churn:"#6656a9"},Yt=()=>({t:-1e9,dir:0,same:0,kind:"",bitT:new Array(8).fill(-1e9),notch:0});function te(t){const e=[];for(let i=0;i+1<t.length;i+=2)e.push(parseInt(t.slice(i,i+2),16));return e}const ee=t=>t.target.value;class ie extends lt{constructor(){super(...arguments),this.interfaces=[],this.offline=[],this.source="",this.paused=!1,this.bin=!1,this.filterText="",this.changingOnly=!1,this.hideInactive=!1,this.expanded=-1,this.message="",this.trace=[],this.traceNext=null,this.traceBusy=!1,this.traceDir="",this.frames=0,this.overflow=0,this.tick=0,this.narrow=!1,this.rows=new Map,this.order=[],this.orderDirty=!0,this.pins=new Set,this.token="",this.subscribed="",this.serverOffset=0,this.traceEnd=null,this.resize=new ResizeObserver(t=>{const e=t[0]?.contentRect.width??1e3;e<640!==this.narrow&&(this.narrow=e<640)}),this.onVisibility=()=>{document.hidden?this.stop():this.paused||this.start()}}connectedCallback(){super.connectedCallback(),document.addEventListener("visibilitychange",this.onVisibility),this.resize.observe(this),this.timer=window.setInterval(()=>{this.paused||document.hidden||this.tick++},200),this.loadPins(),this.source&&!this.paused&&this.start()}disconnectedCallback(){super.disconnectedCallback(),document.removeEventListener("visibilitychange",this.onVisibility),this.resize.disconnect(),window.clearInterval(this.timer),window.clearTimeout(this.retry),this.stop()}updated(t){t.has("source")&&this.source!==this.subscribed&&(this.paused=!1,this.trace=[],this.loadPins(),this.start())}get live(){return this.interfaces.some(t=>t.id===this.source)}get iface(){return this.interfaces.find(t=>t.id===this.source)}loadPins(){this.pins=new Set(kt(`woow_can.pins.${this.source}`,[])),this.orderDirty=!0}savePins(){At(`woow_can.pins.${this.source}`,[...this.pins])}async start(){if(await this.stop(),!this.source||document.hidden)return;const t=this.source;this.rows.clear(),this.orderDirty=!0,this.token=Math.random().toString(36).slice(2,12)+Date.now().toString(36);const e=this.token;this.subscribed=t;try{const i=await this.api.subscribeMonitor(t,e,t=>this.onBatch(t,e));if(this.token!==e)return void i();this.unsub=i}catch(t){this.message=wt(t)}}async stop(){const t=this.unsub;if(this.unsub=void 0,this.token="",t)try{await t()}catch{}}onBatch(t,e){if(e!==this.token)return;if(t.gone)return this.message=t.error??this.t("gone"),window.clearTimeout(this.retry),void(this.retry=window.setTimeout(()=>!this.paused&&void this.start(),1500));const i=performance.now();this.serverOffset=t.t-Date.now()/1e3,(t.full||t.clear)&&(this.rows.clear(),this.orderDirty=!0);for(const e of t.rows??[])this.applyRow(e,i,!!t.full);void 0!==t.frames&&(this.frames=t.frames),void 0!==t.overflow&&(this.overflow=t.overflow),void 0!==t.trace_end&&(this.traceEnd=t.trace_end),this.message===this.t("gone")&&(this.message=""),t.seq>0&&this.api.ack(e,t.seq).catch(()=>{})}applyRow(t,e,i){const[r,s,o,n,a,c,l,d,h,p,u,f]=t,m=te(n);let _=this.rows.get(r);if(_){if(h){const t=c?c/1e6:1;for(let i=0;i<m.length;i++){const r=parseInt(h.slice(2*i,2*i+2)||"0",16);if(!r)continue;const s=_.b[i]??=Yt();for(let t=0;t<8;t++)r>>t&1&&(s.bitT[t]=e);if(!(r&~s.notch&255))continue;const o=_.bytes[i]??0,n=m[i]>o?1:m[i]<o?-1:0,a=e-s.t>10*t*1e3;s.same=0!==n&&n===s.dir?s.same+1:1,s.dir=n,s.kind=0===n?"churn":a||s.same>8?n>0?"rise":"fall":"churn",s.t=e}_.b.length!==m.length&&(_.b=m.map((t,e)=>_.b[e]??Yt()))}}else _={key:r,raw:s,flags:o,hex:n,bytes:m,count:a,period:0,pmin:0,pmax:0,last:p,changed:u,changedPrev:f,born:i?0:e,b:m.map(()=>Yt())},this.rows.set(r,_),this.orderDirty=!0;Object.assign(_,{raw:s,flags:o,hex:n,bytes:m,count:a,last:p,changed:u,changedPrev:f,period:c/1e6,pmin:l/1e6,pmax:d/1e6})}serverNow(){return Date.now()/1e3+this.serverOffset}notch(){const t=performance.now();let e=0;for(const i of this.rows.values())for(const r of i.b)r.bitT.forEach((i,s)=>{t-i<2e3&&!(r.notch>>s&1)&&(r.notch|=1<<s,e++)});this.message=e?this.t("notch_added",{n:e}):this.t("notch_none")}clearNotch(){for(const t of this.rows.values())for(const e of t.b)e.notch=0;this.message=""}async clear(){try{await this.api.clearMonitor(this.source)}catch(t){this.message=wt(t)}}async pause(t){void 0!==t&&(this.filterText=t),this.paused=!0,await this.stop(),this.trace=[],this.traceNext=this.traceEnd,await this.loadTrace(!0)}resume(){this.paused=!1,this.trace=[],this.start()}async loadTrace(t=!1){if(!this.traceBusy){this.traceBusy=!0;try{const e=new bt(this.filterText),i=await this.api.trace(this.source,{before:t?this.traceEnd:this.traceNext,limit:200,ids:e.error||e.all?"":this.filterText,direction:this.traceDir||null});this.trace=t?i.frames:[...this.trace,...i.frames],this.traceNext=i.next}catch(t){this.message=wt(t)}finally{this.traceBusy=!1}}}togglePin(t){this.pins.has(t)?this.pins.delete(t):this.pins.add(t),this.pins=new Set(this.pins),this.savePins(),this.orderDirty=!0,this.requestUpdate()}sendAgain(t){this.dispatchEvent(new CustomEvent("send-frame",{detail:{frame:gt(t.raw,t.flags,t.hex),entryId:this.live?this.source:""}}))}async fireEvents(t){const e=this.iface;if(!e)return;const i=vt(t.raw),r=e.settings.event_filter.trim();try{await this.api.setEvents(e.id,r?`${r}, ${i}`:i),this.message=this.t("events_added",{id:i})}catch(t){this.message=wt(t)}}notchRow(t){for(const e of t.b)e.notch=255;this.requestUpdate()}sorted(){return this.orderDirty&&(this.order=[...this.rows.values()].sort((t,e)=>{const i=this.pins.has(t.key)?0:1,r=this.pins.has(e.key)?0:1;if(i!==r)return i-r;const s=_t(t.raw)?1:0,o=_t(e.raw)?1:0;if(s!==o)return s-o;const n=t.raw%536870912,a=e.raw%536870912;return n!==a?n-a:t.key-e.key}).map(t=>t.key),this.orderDirty=!1),this.order.map(t=>this.rows.get(t)).filter(t=>!!t)}byteCells(t,e){return t.bytes.map((i,r)=>{const s=t.b[r];let o="";if(s?.kind){const t=Math.max(0,1-(e-s.t)/Qt)*("churn"===s.kind?.4:.65);t>.01&&(o=`background: color-mix(in srgb, ${Gt[s.kind]} ${Math.round(100*t)}%, transparent)`)}const n=this.bin?i.toString(2).padStart(8,"0"):i.toString(16).toUpperCase().padStart(2,"0");return W`<span class="byte ${this.bin?"bin":""} ${s?.notch?"notched":""}" style=${o}>${n}</span>`})}detailRow(t,e){return W`<tr class="detail"><td colspan="9">${this.detail(t,e)}</td></tr>`}detail(t,e){const i=this.t,r=this.pins.has(t.key),s=this.iface,o=s?new bt(s.settings.event_filter):null,n=!!(s&&s.settings.event_filter.trim()&&o&&!o.error&&o.matches(t.raw));return W`
        <div class="mono">${gt(t.raw,t.flags,t.hex)}</div>
        <div class="muted">
          ${t.period?W`${i("detail_period",{avg:(1e3*t.period).toFixed(t.period<.1?2:1),min:(1e3*t.pmin).toFixed(1),max:(1e3*t.pmax).toFixed(1)})} · ${i("detail_rate",{hz:(1/t.period).toFixed(2)})}`:K}
        </div>
        ${t.changedPrev?W`<div class="muted">
              ${i("detail_changed",{ago:Nt(t.changed,i,e),gap:Dt(t.changed-t.changedPrev)})}
            </div>`:K}
        <div class="actions">
          <button @click=${()=>this.togglePin(t.key)}>${i(r?"row_unpin":"row_pin")}</button>
          <button @click=${()=>this.sendAgain(t)}>${i("row_send")}</button>
          ${s?W`<button ?disabled=${n} @click=${()=>this.fireEvents(t)}>
                ${i(n?"row_events_on":"row_events")}
              </button>`:K}
          <button @click=${()=>this.pause(vt(t.raw))}>${i("row_trace")}</button>
          <button @click=${()=>this.notchRow(t)}>${i("row_notch")}</button>
        </div>`}renderLive(){const t=this.t,e=performance.now(),i=this.serverNow(),r=new bt(this.filterText),s=this.sorted().filter(t=>!(!r.error&&!r.matches(t.raw))&&((!this.changingOnly||t.changedPrev>0&&i-t.changed<5)&&!(this.hideInactive&&i-t.last>5)));return this.rows.size?this.narrow?this.renderCards(s,e,i):W`<div class="wrap">
      <table>
        <thead>
          <tr>
            <th></th>
            <th>${t("col_id")}</th>
            <th>${t("col_len")}</th>
            <th>${t("col_data")}</th>
            <th class="num">${t("col_count")}</th>
            <th class="num">${t("col_hz")}</th>
            <th class="num">${t("col_period")}</th>
            <th class="num">${t("col_dchg")}</th>
            <th class="num">${t("col_age")}</th>
          </tr>
        </thead>
        <tbody>
          ${Xt(s,t=>t.key,r=>{const s=i-r.last,o=s>(r.period?5*r.period+.5:1.75),n=r.key>=mt,a=!n&&!!(8&r.flags)&&!this.iface?.virtual;return W`<tr class="${o?"inactive":""} ${r.born&&e-r.born<Qt?"new":""}">
                  <td><button class="pin ${this.pins.has(r.key)?"on":""}" title=${t("row_pin")}
                    @click=${()=>this.togglePin(r.key)}>${this.pins.has(r.key)?"★":"☆"}</button></td>
                  <td class="id ${s>4?"stale":""}" @click=${()=>this.expanded=this.expanded===r.key?-1:r.key}>
                    ${vt(r.raw)}${n?W`<span class="tag">${t("dir_tx")}</span>`:K}${a?W`<span class="tag muted-tag">${t("dir_local")}</span>`:K}
                  </td>
                  <td class="num">${r.bytes.length}</td>
                  <td><div class="bytes">${this.byteCells(r,e)}</div></td>
                  <td class="num">${r.count.toLocaleString()}</td>
                  <td class="num">${r.period?(1/r.period).toFixed(1):"–"}</td>
                  <td class="num">${r.period?Dt(r.period):"–"}</td>
                  <td class="num">${r.changedPrev?Dt(r.changed-r.changedPrev):"–"}</td>
                  <td class="num">${Dt(Math.max(0,s))}</td>
                </tr>
                ${this.expanded===r.key?this.detailRow(r,i):K}`})}
        </tbody>
      </table>
    </div>`:W`<div class="empty">${t("monitor_empty")}</div>`}renderCards(t,e,i){const r=this.t;return W`<div class="cards">
      ${Xt(t,t=>t.key,t=>{const s=i-t.last,o=s>(t.period?5*t.period+.5:1.75),n=t.key>=mt;return W`<div class="mrow ${o?"inactive":""} ${t.born&&e-t.born<Qt?"new":""}">
            <div class="mhead" @click=${()=>this.expanded=this.expanded===t.key?-1:t.key}>
              <button class="pin ${this.pins.has(t.key)?"on":""}" @click=${e=>{e.stopPropagation(),this.togglePin(t.key)}}>${this.pins.has(t.key)?"★":"☆"}</button>
              <span class="id ${s>4?"stale":""}">${vt(t.raw)}</span>
              ${n?W`<span class="tag">${r("dir_tx")}</span>`:K}
              <span class="grow"></span>
              <span class="muted">${t.period?`${(1/t.period).toFixed(1)} Hz · `:""}${Dt(Math.max(0,s))}</span>
            </div>
            <div class="bytes wrapbytes">${this.byteCells(t,e)}</div>
            ${this.expanded===t.key?W`<div class="mdetail">${this.detail(t,i)}</div>`:K}
          </div>`})}
    </div>`}renderTrace(){const t=this.t,e=this.trace;return W`<div class="row msg">
        <b class="grow">${t("paused_title")}</b>
        <select @change=${t=>{this.traceDir=ee(t),this.loadTrace(!0)}}>
          <option value="" ?selected=${!this.traceDir}>${t("trace_all_dirs")}</option>
          <option value="rx" ?selected=${"rx"===this.traceDir}>${t("dir_rx")}</option>
          <option value="tx" ?selected=${"tx"===this.traceDir}>${t("dir_tx")}</option>
        </select>
      </div>
      ${0===e.length?W`<div class="empty">${this.traceBusy?t("loading"):t("trace_empty")}</div>`:W`<div class="wrap">
            <table>
              <thead>
                <tr>
                  <th>${t("trace_time")}</th>
                  ${this.narrow?K:W`<th class="num">${t("trace_delta")}</th>`}
                  <th>${t("col_dir")}</th>
                  <th>${t("col_id")}</th>
                  ${this.narrow?K:W`<th>${t("col_len")}</th>`}
                  <th>${t("col_data")}</th>
                </tr>
              </thead>
              <tbody>
                ${e.map(([i,r,s,o,n],a)=>{const c=e[a+1],l=!!(16&o),d=!!(4&o);return W`<tr title=${`#${i}`}>
                    <td class="num">${Pt(r)}</td>
                    ${this.narrow?K:W`<td class="num">${c?Dt(r-c[1]):""}</td>`}
                    <td>${t(d?"dir_tx":"dir_rx")}</td>
                    <td class="id">${l?W`<span class="tag err">ERR</span>`:vt(s)}</td>
                    ${this.narrow?K:W`<td class="num">${n.length/2}</td>`}
                    <td><div class="bytes">
                      ${l?W`<span class="muted">${t("trace_error",{x:gt(s,o,n)})}</span>`:te(n).map(t=>W`<span class="byte ${this.bin?"bin":""}">${this.bin?t.toString(2).padStart(8,"0"):t.toString(16).toUpperCase().padStart(2,"0")}</span>`)}
                    </div></td>
                  </tr>`})}
              </tbody>
            </table>
          </div>`}
      <div class="row msg">
        ${null!==this.traceNext?W`<button ?disabled=${this.traceBusy} @click=${()=>this.loadTrace()}>${t("trace_older")}</button>`:e.length?W`<span class="muted">${t("trace_start")}</span>`:K}
      </div>`}render(){const t=this.t;this.tick;const e=this.offline.find(t=>t.id===this.source),i=new bt(this.filterText);return W`<div class="card">
      <div class="toolbar">
        <select title=${t("source")} @change=${t=>this.dispatchEvent(new CustomEvent("source-changed",{detail:ee(t)}))}>
          ${this.interfaces.map(t=>W`<option value=${t.id} ?selected=${t.id===this.source}>${t.name} · ${t.port}</option>`)}
          ${this.offline.map(e=>W`<option value=${e.id} ?selected=${e.id===this.source}>${t("file_source",{name:e.name})}</option>`)}
        </select>
        ${this.paused?W`<button class="primary" @click=${()=>this.resume()}>${t("resume")}</button>`:W`<button @click=${()=>this.pause()}>${t("pause")}</button>`}
        ${this.live&&!this.paused?W`<button @click=${()=>this.clear()}>${t("clear")}</button>`:K}
        ${this.paused?K:W`<button @click=${()=>this.notch()}>${t("notch")}</button>
              <button @click=${()=>this.clearNotch()}>${t("notch_clear")}</button>
              <label class="toggle"><input type="checkbox" .checked=${this.changingOnly}
                @change=${t=>this.changingOnly=t.target.checked} />${t("changing_only")}</label>
              <label class="toggle"><input type="checkbox" .checked=${this.hideInactive}
                @change=${t=>this.hideInactive=t.target.checked} />${t("hide_inactive")}</label>`}
        <label class="toggle"><input type="checkbox" .checked=${this.bin}
          @change=${t=>this.bin=t.target.checked} />${t("view_bin")}</label>
        <input type="search" placeholder=${t("filter_ph")} .value=${this.filterText}
          @input=${t=>this.filterText=ee(t)}
          @change=${()=>this.paused&&this.loadTrace(!0)} />
      </div>
      ${i.error?W`<div class="chip bad">${t("filter_bad",{x:i.error})}</div>`:K}
      <div class="muted">
        ${t("frames_total",{ids:this.rows.size,n:this.frames.toLocaleString()})}
        ${this.overflow?W` · ${t("overflow",{n:this.overflow})}`:K}
        ${e?W` · ${t("offline_note",{file:e.file,n:e.frames})}`:K}
      </div>
      ${this.message?W`<div class="msg chip info" style="white-space:normal">${this.message}</div>`:K}
      ${this.paused?this.renderTrace():this.renderLive()}
      ${this.paused?K:W`<p class="muted">${t("monitor_hint")}</p>`}
    </div>`}}ie.styles=[Ot,Rt,n`
      .toolbar {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }
      .toolbar input[type="search"] {
        flex: 1 1 14em;
      }
      label.toggle {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.92em;
        white-space: nowrap;
      }
      .wrap {
        overflow-x: auto;
      }
      table {
        border-collapse: collapse;
        width: 100%;
        font-size: 0.92em;
      }
      th,
      td {
        text-align: left;
        padding: 4px 8px;
        border-bottom: 1px solid var(--divider-color, #eee);
        white-space: nowrap;
        vertical-align: middle;
      }
      th {
        color: var(--secondary-text-color);
        font-weight: 500;
        font-size: 0.9em;
      }
      td.num {
        text-align: right;
        font-variant-numeric: tabular-nums;
      }
      td.id {
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        font-weight: 600;
        cursor: pointer;
      }
      td.id.stale {
        color: var(--error-color, #db4437);
      }
      tr.inactive td {
        opacity: 0.45;
      }
      tr.new td {
        background: rgba(3, 169, 244, 0.08);
      }
      tr.detail td {
        white-space: normal;
        background: var(--secondary-background-color, #f5f5f5);
      }
      .pin {
        border: none;
        background: none;
        padding: 0 2px;
        color: var(--secondary-text-color);
      }
      .pin.on {
        color: var(--warning-color, #ff9800);
      }
      .tag {
        font-size: 0.75em;
        padding: 0 6px;
        border-radius: 8px;
        background: rgba(3, 169, 244, 0.14);
        color: var(--info-color, #039be5);
        margin-left: 4px;
        font-weight: 400;
      }
      .tag.muted-tag {
        background: var(--secondary-background-color, #eee);
        color: var(--secondary-text-color);
      }
      .tag.err {
        background: rgba(219, 68, 55, 0.12);
        color: var(--error-color, #db4437);
      }
      .msg {
        margin: 6px 0;
      }
      .cards {
        display: grid;
        gap: 6px;
      }
      .mrow {
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 8px;
        padding: 6px 8px;
        display: grid;
        gap: 4px;
      }
      .mrow.inactive {
        opacity: 0.5;
      }
      .mrow.new {
        background: rgba(3, 169, 244, 0.08);
      }
      .mhead {
        display: flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
      }
      .mhead .id {
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        font-weight: 600;
      }
      .mhead .id.stale {
        color: var(--error-color, #db4437);
      }
      .wrapbytes {
        flex-wrap: wrap;
      }
      .mdetail {
        padding-top: 6px;
        border-top: 1px solid var(--divider-color, #eee);
        font-size: 0.92em;
      }
      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 6px;
      }
    `],t([ut({attribute:!1})],ie.prototype,"interfaces",void 0),t([ut({attribute:!1})],ie.prototype,"offline",void 0),t([ut({attribute:!1})],ie.prototype,"source",void 0),t([ut({attribute:!1})],ie.prototype,"t",void 0),t([ut({attribute:!1})],ie.prototype,"api",void 0),t([ft()],ie.prototype,"paused",void 0),t([ft()],ie.prototype,"bin",void 0),t([ft()],ie.prototype,"filterText",void 0),t([ft()],ie.prototype,"changingOnly",void 0),t([ft()],ie.prototype,"hideInactive",void 0),t([ft()],ie.prototype,"expanded",void 0),t([ft()],ie.prototype,"message",void 0),t([ft()],ie.prototype,"trace",void 0),t([ft()],ie.prototype,"traceNext",void 0),t([ft()],ie.prototype,"traceBusy",void 0),t([ft()],ie.prototype,"traceDir",void 0),t([ft()],ie.prototype,"frames",void 0),t([ft()],ie.prototype,"overflow",void 0),t([ft()],ie.prototype,"tick",void 0),t([ft()],ie.prototype,"narrow",void 0),xt("woow-can-monitor",ie);const re={error_active:"ok",error_warning:"warn",error_passive:"warn",bus_off:"bad",stopped:"",sleeping:"",virtual:"info"};class se extends lt{constructor(){super(...arguments),this.interfaces=[],this.history={}}stateLabel(t){if(!t.available)return this.t("unavailable");const e=String(t.status.state??"unknown"),i=`state_${e}`;return Mt(i)?this.t(i):e}sparkline(t){if(t.length<2)return K;const e=Math.max(10,...t),i=300,r=36,s=i/(t.length-1),o=t.map((t,i)=>`${(i*s).toFixed(1)},${(34-t/e*32).toFixed(1)}`);return W`<svg class="spark" viewBox="0 0 ${i} ${r}" preserveAspectRatio="none" role="img" aria-label=${this.t("sparkline")}>
      ${q`<line x1="0" y1=${35} x2=${i} y2=${35}></line>
        <polygon points=${`0,35 ${o.join(" ")} 300,35`}></polygon>
        <polyline points=${o.join(" ")}></polyline>`}
    </svg>`}hints(t){const e=this.t,i=t.status,r=[];return t.settings.listen_only&&!t.virtual&&r.push({cls:"info",text:e("hint_listen_only")}),"bus_off"===i.state?r.push({cls:"bad",text:t.settings.restart_ms?e("hint_bus_off_auto",{ms:t.settings.restart_ms}):e("hint_bus_off_manual")}):"error_passive"===i.state&&Number(i.tx_error_counter??0)>=128&&r.push({cls:"warn",text:e("hint_passive")}),Number(i.rx_over_errors??0)>0&&r.push({cls:"warn",text:e("hint_overflow",{n:Number(i.rx_over_errors)})}),Number(i.socket_drops??0)>0&&r.push({cls:"warn",text:e("hint_socket_drops",{n:Number(i.socket_drops)})}),r}card(t){const e=this.t,i=t.status,r=t.load,s=i.berr_reporting?`${i.bus_error??0} · ${e("arbitration_lost")} ${i.arbitration_lost??0}`:i.berr_supported?e("reporting_off"):e("not_supported"),o=t.virtual?[e("virtual_iface")]:[e("kbps",{n:Math.round(t.settings.bitrate/1e3)}),...t.settings.fd?[e("can_fd")]:[],...t.settings.listen_only?[e("listen_only")]:[]],n=t.errors.last,a=String(i.state??"");return W`<div class="card">
      <div class="head">
        <b>${t.name}</b>
        <span class="muted">${t.port} · ${t.driver||"?"} · ${o.join(" · ")}</span>
        <span class="grow"></span>
        <button class="link" @click=${()=>this.dispatchEvent(new CustomEvent("open-monitor",{detail:t.id}))}>
          ${e("open_monitor")}
        </button>
      </div>
      <div class="row">
        <span class="chip ${t.available?re[a]??"":"bad"}">${this.stateLabel(t)}</span>
        ${null!=i.tx_error_counter?W`<span class="muted">${e("tec_rec")} ${i.tx_error_counter} / ${i.rx_error_counter}</span>`:K}
        ${t.recording?W`<span class="chip bad">● ${e("recording_now",{name:t.recording.name,n:t.recording.frames})}</span>`:K}
      </div>
      ${this.hints(t).map(t=>W`<div class="hint ${t.cls}">${t.text}</div>`)}
      ${t.virtual?K:W`<div>
            <div class="row">
              <span>${e("load")}</span><span class="grow"></span>
              <b>${Tt(r.now)}</b>
            </div>
            <div class="bar ${(r.now??0)>70?"hot":""}" title=${e("load_hint")}>
              <i style="width:${Math.min(100,r.now??0)}%"></i>
            </div>
            <div class="muted" style="margin-top:4px">
              ${e("load_values",{now:Tt(r.now),peak:Tt(r.peak),a1:Tt(r.avg[0]),a5:Tt(r.avg[1]),a15:Tt(r.avg[2])})}
            </div>
            ${this.sparkline(this.history[t.id]??[])}
          </div>`}
      <dl>
        <dt>${e("traffic")}</dt>
        <dd>${e("rates",{rx:(r.rx_fps??0).toFixed(1),tx:(r.tx_fps??0).toFixed(1)})}</dd>
        <dt>${e("seen")}</dt>
        <dd>${e("ids_seen",{n:t.monitor.ids,f:t.monitor.frames.toLocaleString()})}</dd>
        ${t.virtual?K:W`<dt>${e("controller_events")}</dt>
              <dd>${i.error_warning??"–"} / ${i.error_passive??"–"} / ${i.bus_off??"–"} / ${i.restarts??"–"}</dd>
              <dt>${e("bus_errors")}</dt>
              <dd>${s}</dd>`}
        <dt>${e("drops")}</dt>
        <dd>${i.socket_drops??0} / ${i.rx_over_errors??0} / ${i.events_dropped??0}</dd>
        <dt>${e("last_error")}</dt>
        <dd>
          ${n?W`<span title=${`${Pt(n.t)} · ${n.frame}`}
                >${n.codes.map(t=>function(t,e){const i=`err_${t}`;return Mt(i)?e(i):t}(t,e)).join("、")} · ${Nt(n.t,e)}</span
              >`:e("none")}
        </dd>
      </dl>
      <div class="muted">
        ${t.settings.event_filter?e("events_filter",{x:t.settings.event_filter}):e("events_none")}
        ${i.clock?W` · ${e("clock_mhz",{n:Number(i.clock)/1e6})}`:K}
        ${i.sample_point?W` · ${e("sample_point",{n:(100*Number(i.sample_point)).toFixed(1)})}`:K}
      </div>
    </div>`}render(){return this.interfaces.length?W`<div class="cards">${this.interfaces.map(t=>this.card(t))}</div>`:W`<div class="card"><div class="empty">${this.t("no_interfaces")}</div></div>`}}se.styles=[Ot,n`
      .cards {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(min(100%, 340px), 1fr));
        gap: 16px;
      }
      .card {
        margin: 0;
        display: grid;
        gap: 10px;
        align-content: start;
      }
      .head {
        display: flex;
        flex-wrap: wrap;
        align-items: baseline;
        gap: 6px 10px;
      }
      .head b {
        font-size: 1.15em;
      }
      .bar {
        height: 8px;
        border-radius: 99px;
        background: var(--secondary-background-color, #eee);
        overflow: hidden;
      }
      .bar i {
        display: block;
        height: 100%;
        background: var(--primary-color);
        transition: width 0.3s;
      }
      .bar.hot i {
        background: var(--warning-color, #ff9800);
      }
      dl {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: 4px 12px;
        margin: 0;
        font-size: 0.92em;
      }
      dt {
        color: var(--secondary-text-color);
      }
      dd {
        margin: 0;
        text-align: right;
        font-variant-numeric: tabular-nums;
      }
      @media (max-width: 520px) {
        dl {
          grid-template-columns: 1fr;
          gap: 0;
        }
        dt {
          margin-top: 6px;
        }
        dd {
          text-align: left;
        }
      }
      .hint {
        font-size: 0.9em;
        line-height: 1.5;
        padding: 6px 10px;
        border-radius: 8px;
        background: rgba(255, 152, 0, 0.12);
      }
      .hint.bad {
        background: rgba(219, 68, 55, 0.12);
      }
      .hint.info {
        background: rgba(3, 169, 244, 0.1);
      }
      svg.spark {
        width: 100%;
        height: 36px;
        display: block;
      }
      .spark polyline {
        fill: none;
        stroke: var(--primary-color);
        stroke-width: 1.5;
      }
      .spark polygon {
        fill: var(--primary-color);
        opacity: 0.12;
      }
      .spark line {
        stroke: var(--divider-color, #ddd);
        stroke-width: 1;
      }
    `],t([ut({attribute:!1})],se.prototype,"interfaces",void 0),t([ut({attribute:!1})],se.prototype,"history",void 0),t([ut({attribute:!1})],se.prototype,"t",void 0),xt("woow-can-overview",se);const oe=t=>t.target.value;class ne extends lt{constructor(){super(...arguments),this.interfaces=[],this.periodic=[],this.confirmed=new Set,this.draft=null,this.entryId="",this.frame="",this.waitId="",this.waitMs=0,this.busy=!1,this.result=null,this.confirming=!1,this.edit=null,this.editError="",this.listError="",this.draftSeen=0}willUpdate(t){t.has("draft")&&this.draft&&this.draft.n!==this.draftSeen&&(this.draftSeen=this.draft.n,this.frame=this.draft.frame,this.draft.entryId&&(this.entryId=this.draft.entryId),this.result=null),this.entryId&&this.interfaces.some(t=>t.id===this.entryId)||(this.entryId=(this.interfaces.find(t=>t.can_send)??this.interfaces[0])?.id??"")}get iface(){return this.interfaces.find(t=>t.id===this.entryId)}whyNot(t){return t?t.available?t.can_send?"":this.t("why_listen"):this.t("why_unavailable"):""}trySend(){this.frame.trim()&&this.iface&&(this.confirmed.has(this.entryId)?this.send():this.confirming=!0)}async send(){const t=this.t;this.confirming=!1,this.dispatchEvent(new CustomEvent("confirmed",{detail:this.entryId})),this.busy=!0,this.result=null;try{const e=await this.api.send(this.entryId,this.frame.trim(),this.waitMs,this.waitId.trim());let i=t("sent_ok",{frame:e.sent.frame});(this.waitMs>0||this.waitId)&&(i+="\n"+(e.reply?t("reply",{frame:e.reply.frame}):t("no_reply"))),this.result={ok:!0,text:i}}catch(e){this.result={ok:!1,text:t("error",{msg:wt(e)})}}finally{this.busy=!1}}newDraft(){this.editError="",this.edit={name:"",entry_id:this.entryId,frame:this.frame.trim(),period_ms:1e3,count:0}}async saveDraft(){if(this.edit)try{await this.api.savePeriodic(this.edit),this.edit=null,this.editError=""}catch(t){this.editError=wt(t)}}async control(t,e){this.listError="";try{await this.api.controlPeriodic(t.id,e)}catch(e){this.listError=`${t.name}: ${wt(e)}`}}state(t){const e=this.t;return t.running?e("running"):"count"===t.stopped_by?e("stopped_by_count"):"error"===t.stopped_by?e("stopped_by_error",{x:t.error??"?"}):"interface"===t.stopped_by?e("stopped_by_interface"):e("stopped")}renderEditor(){const t=this.t,e=this.edit;if(!e)return K;const i=t=>this.edit={...e,...t};return W`<div class="editor">
      <label>${t("name")}<input .value=${e.name} @input=${t=>i({name:oe(t)})} /></label>
      <label>${t("interface")}
        <select @change=${t=>i({entry_id:oe(t)})}>
          ${this.interfaces.map(t=>W`<option value=${t.id} ?selected=${t.id===e.entry_id}>${t.name}</option>`)}
        </select>
      </label>
      <label>${t("frame")}<input class="mono" placeholder=${t("frame_ph")} .value=${e.frame}
        @input=${t=>i({frame:oe(t)})} /></label>
      <label>${t("period_ms")}<input type="number" min="10" .value=${String(e.period_ms)}
        @input=${t=>i({period_ms:Number(oe(t))})} /></label>
      <label>${t("count")}<input type="number" min="0" .value=${String(e.count)}
        @input=${t=>i({count:Number(oe(t))})} /></label>
      <div class="row">
        <button class="primary" @click=${()=>this.saveDraft()}>${t("save")}</button>
        <button @click=${()=>this.edit=null}>${t("cancel")}</button>
      </div>
      ${this.editError?W`<div class="chip bad" style="white-space:normal">${this.editError}</div>`:K}
    </div>`}render(){const t=this.t,e=this.iface,i=this.whyNot(e),r=t=>this.interfaces.find(e=>e.id===t)?.name??"?";return W`<div class="card">
        <h2>${t("send_title")}</h2>
        <div class="form">
          <label>${t("interface")}
            <select @change=${t=>this.entryId=oe(t)}>
              ${this.interfaces.map(e=>W`<option value=${e.id} ?selected=${e.id===this.entryId}>
                ${e.name}${e.can_send?"":` (${t("listen_only")})`}</option>`)}
            </select>
          </label>
          <label class="wide">${t("frame")}
            <input class="mono" placeholder=${t("frame_ph")} .value=${this.frame}
              @input=${t=>this.frame=oe(t)}
              @keydown=${t=>"Enter"===t.key&&this.trySend()} />
          </label>
          <label>${t("wait_id")}<input class="mono" placeholder="7E8" .value=${this.waitId}
            @input=${t=>this.waitId=oe(t)} /></label>
          <label>${t("wait_ms")}<input type="number" min="0" step="100" .value=${String(this.waitMs)}
            @input=${t=>this.waitMs=Math.max(0,Number(oe(t))||0)} /></label>
          <button class="primary" ?disabled=${this.busy||!!i||!this.frame.trim()} @click=${()=>this.trySend()}>
            ${t("send")}
          </button>
        </div>
        <p class="muted">${t("frame_help")}</p>
        ${i&&e?W`<div class="chip warn" style="white-space:normal">${t("cannot_send",{name:e.name,why:i})}</div>`:K}
        ${this.result?W`<div class="result ${this.result.ok?"":"bad"}">${this.result.text}</div>`:K}
      </div>
      <div class="card">
        <div class="row">
          <h2 class="grow">${t("periodic_title")}</h2>
          <button @click=${()=>this.newDraft()}>${t("add")}</button>
        </div>
        <div class="muted">${t("periodic_hint")}</div>
        ${this.renderEditor()}
        ${this.listError?W`<div class="chip bad" style="white-space:normal">${this.listError}</div>`:K}
        ${0===this.periodic.length?W`<div class="empty">${t("periodic_empty")}</div>`:W`<div class="wrap"><table>
              <thead><tr>
                <th>${t("name")}</th><th>${t("interface")}</th><th>${t("frame")}</th><th>${t("period_ms")}</th>
                <th>${t("count")}</th><th></th><th></th>
              </tr></thead>
              <tbody>
                ${this.periodic.map(e=>W`<tr>
                  <td>${e.name}</td>
                  <td>${r(e.entry_id)}</td>
                  <td class="mono">${e.frame}</td>
                  <td>${e.period_ms}</td>
                  <td>${e.count||"∞"}</td>
                  <td>
                    <span class="chip ${e.running?"ok":"error"===e.stopped_by?"bad":""}">${this.state(e)}</span>
                    <span class="muted">${t("sent_n",{n:e.sent})}</span>
                  </td>
                  <td class="row">
                    ${e.running?W`<button @click=${()=>this.control(e,"stop")}>${t("stop")}</button>`:W`<button class="primary" @click=${()=>this.control(e,"start")}>${t("start")}</button>`}
                    <button class="link" @click=${()=>{this.editError="",this.edit={id:e.id,name:e.name,entry_id:e.entry_id,frame:e.frame,period_ms:e.period_ms,count:e.count}}}>${t("edit")}</button>
                    <button class="link danger" @click=${()=>this.control(e,"delete")}>${t("delete")}</button>
                  </td>
                </tr>`)}
              </tbody>
            </table></div>`}
      </div>
      ${this.confirming&&e?W`<div class="scrim" @click=${t=>t.target===t.currentTarget&&(this.confirming=!1)}>
            <div class="dialog">
              <h2>${t("confirm_title",{name:e.name})}</h2>
              <div class="mono">${this.frame}</div>
              <div>${t("confirm_text")}</div>
              <div class="row">
                <span class="grow"></span>
                <button @click=${()=>this.confirming=!1}>${t("cancel")}</button>
                <button class="primary" @click=${()=>this.send()}>${t("confirm_ok")}</button>
              </div>
            </div>
          </div>`:K}`}}ne.styles=[Ot,n`
      .form {
        display: grid;
        grid-template-columns: minmax(8em, 1fr) minmax(12em, 3fr) minmax(6em, 1fr) minmax(6em, 1fr) auto;
        gap: 8px;
        align-items: end;
      }
      @media (max-width: 720px) {
        .form {
          grid-template-columns: 1fr 1fr;
        }
        .form .wide {
          grid-column: 1 / -1;
        }
      }
      label {
        display: grid;
        gap: 4px;
        font-size: 0.85em;
        color: var(--secondary-text-color);
      }
      label input,
      label select {
        font-size: 1.05em;
        color: var(--primary-text-color);
      }
      .result {
        margin-top: 10px;
        padding: 8px 10px;
        border-radius: 8px;
        background: rgba(67, 160, 71, 0.12);
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        white-space: pre-wrap;
      }
      .result.bad {
        background: rgba(219, 68, 55, 0.12);
        font-family: inherit;
      }
      .wrap {
        overflow-x: auto;
      }
      table {
        border-collapse: collapse;
        width: 100%;
      }
      th,
      td {
        text-align: left;
        padding: 6px 8px;
        border-bottom: 1px solid var(--divider-color, #eee);
        white-space: nowrap;
      }
      th {
        color: var(--secondary-text-color);
        font-weight: 500;
        font-size: 0.9em;
      }
      .scrim {
        position: fixed;
        inset: 0;
        z-index: 10;
        background: rgba(0, 0, 0, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 16px;
      }
      .dialog {
        width: min(460px, 100%);
        background: var(--card-background-color, #fff);
        border-radius: 12px;
        padding: 20px;
        display: grid;
        gap: 12px;
      }
      .dialog h2 {
        margin: 0;
        font-size: 1.15em;
        font-weight: 500;
      }
      .editor {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(10em, 1fr));
        gap: 8px;
        align-items: end;
        margin-top: 12px;
        padding: 12px;
        border-radius: 10px;
        background: var(--secondary-background-color, #f5f5f5);
      }
    `],t([ut({attribute:!1})],ne.prototype,"interfaces",void 0),t([ut({attribute:!1})],ne.prototype,"periodic",void 0),t([ut({attribute:!1})],ne.prototype,"confirmed",void 0),t([ut({attribute:!1})],ne.prototype,"draft",void 0),t([ut({attribute:!1})],ne.prototype,"t",void 0),t([ut({attribute:!1})],ne.prototype,"api",void 0),t([ft()],ne.prototype,"entryId",void 0),t([ft()],ne.prototype,"frame",void 0),t([ft()],ne.prototype,"waitId",void 0),t([ft()],ne.prototype,"waitMs",void 0),t([ft()],ne.prototype,"busy",void 0),t([ft()],ne.prototype,"result",void 0),t([ft()],ne.prototype,"confirming",void 0),t([ft()],ne.prototype,"edit",void 0),t([ft()],ne.prototype,"editError",void 0),t([ft()],ne.prototype,"listError",void 0),xt("woow-can-send",ne);const ae=["overview","monitor","send","capture","activity"];class ce extends lt{constructor(){super(...arguments),this.narrow=!1,this.tab=kt("woow_can.tab","overview"),this.interfaces={},this.offline=[],this.periodic={},this.activity=[],this.files=[],this.history={},this.source=kt("woow_can.source",""),this.draft=null,this.confirmed=new Set,this.loaded=!1,this.error="",this.t=Ct("en"),this.api=new yt(()=>this._hass),this.connecting=!1}set hass(t){const e=!this._hass;this._hass=t,e&&(this.t=Ct(t.locale?.language??t.language??"en"),this.isConnected&&this.connect(),this.requestUpdate())}get hass(){return this._hass}connectedCallback(){super.connectedCallback(),this._hass&&!this.unsubscribe&&this.connect()}disconnectedCallback(){super.disconnectedCallback(),this.unsubscribe?.(),this.unsubscribe=void 0}async connect(){if(!this.connecting&&!this.unsubscribe){this.connecting=!0;try{this.unsubscribe=await this.api.subscribe(t=>this.onEvent(t));const t=await this.api.snapshot();this.interfaces=Object.fromEntries(t.interfaces.map(t=>[t.id,t])),this.offline=t.offline,this.periodic=Object.fromEntries(t.periodic.map(t=>[t.id,t])),this.activity=t.activity,this.source&&(this.source in this.interfaces||t.offline.some(t=>t.id===this.source))||(this.source=this.interfaceList[0]?.id??""),this.loaded=!0,this.error="",this.loadFiles()}catch(t){this.error=wt(t)}finally{this.connecting=!1}}}async loadFiles(){try{const t=await this.api.captures();this.files=t.captures,this.offline=t.offline}catch{}}onEvent(t){switch(t.kind){case"interfaces":{const e={...this.interfaces},i={...this.history};for(const r of t.interfaces)e[r.id]=r,null!=r.load.now&&(i[r.id]=[...i[r.id]??[],r.load.now].slice(-300));for(const i of t.removed)delete e[i];this.interfaces=e,this.history=i,!this.source&&t.interfaces.length&&(this.source=t.interfaces[0].id);break}case"periodic":{const e={...this.periodic};for(const i of t.items)e[i.id]=i;for(const i of t.removed)delete e[i];this.periodic=e;break}case"activity":this.activity=[...t.entries.reverse(),...this.activity].slice(0,500);break;case"captures":this.loadFiles();break;case"offline":this.offline=t.offline,this.source.startsWith("file:")&&!t.offline.some(t=>t.id===this.source)&&(this.source=this.interfaceList[0]?.id??"")}}get interfaceList(){return Object.values(this.interfaces).sort((t,e)=>t.name.localeCompare(e.name))}setTab(t){this.tab=t,At("woow_can.tab",t)}setSource(t){this.source=t,At("woow_can.source",t)}toggleMenu(){this.dispatchEvent(new Event("hass-toggle-menu",{bubbles:!0,composed:!0}))}renderTab(){const t=this.interfaceList;switch(this.tab){case"monitor":return W`<woow-can-monitor
          .interfaces=${t}
          .offline=${this.offline}
          .source=${this.source}
          .t=${this.t}
          .api=${this.api}
          @source-changed=${t=>this.setSource(t.detail)}
          @send-frame=${t=>{this.draft={...t.detail,n:(this.draft?.n??0)+1},this.setTab("send")}}
        ></woow-can-monitor>`;case"send":return W`<woow-can-send
          .interfaces=${t}
          .periodic=${Object.values(this.periodic)}
          .confirmed=${this.confirmed}
          .draft=${this.draft}
          .t=${this.t}
          .api=${this.api}
          @confirmed=${t=>this.confirmed=new Set([...this.confirmed,t.detail])}
        ></woow-can-send>`;case"capture":return W`<woow-can-capture
          .interfaces=${t}
          .offline=${this.offline}
          .files=${this.files}
          .t=${this.t}
          .api=${this.api}
          @captures-changed=${()=>this.loadFiles()}
          @open-source=${t=>{this.setSource(t.detail),this.setTab("monitor")}}
        ></woow-can-capture>`;case"activity":return W`<woow-can-activity
          .entries=${this.activity}
          .t=${this.t}
          .portName=${t=>this.interfaces[t]?.name??"?"}
        ></woow-can-activity>`;default:return W`<woow-can-overview
          .interfaces=${t}
          .history=${this.history}
          .t=${this.t}
          @open-monitor=${t=>{this.setSource(t.detail),this.setTab("monitor")}}
        ></woow-can-overview>`}}render(){const t=this.t,e={send:Object.values(this.periodic).filter(t=>t.running).length,capture:this.files.length};return W`
      <div class="toolbar">
        ${this.narrow?W`<button @click=${this.toggleMenu} aria-label="menu">
              <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d=${"M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z"}></path></svg>
            </button>`:K}
        <div>${t("title")}</div>
      </div>
      <div class="tabs">
        ${ae.map(i=>W`<button class="tab ${this.tab===i?"active":""}" @click=${()=>this.setTab(i)}>
            ${t(`tab_${i}`)}${e[i]?W`<span class="count">${e[i]}</span>`:K}
          </button>`)}
      </div>
      <div class="content">
        ${this.error?W`<div class="card"><div class="chip bad">${t("error",{msg:this.error})}</div></div>`:this.loaded?this.renderTab():W`<div class="empty">${t("loading")}</div>`}
      </div>
    `}}ce.styles=[Ot,n`
      :host {
        min-height: 100vh;
        background: var(--primary-background-color);
      }
      .toolbar {
        display: flex;
        align-items: center;
        gap: 8px;
        height: 56px;
        padding: 0 16px;
        background: var(--app-header-background-color, var(--primary-color));
        color: var(--app-header-text-color, var(--text-primary-color, #fff));
        font-size: 20px;
      }
      .toolbar button {
        border: none;
        background: none;
        color: inherit;
        padding: 8px;
        line-height: 0;
      }
      .tabs {
        display: flex;
        gap: 4px;
        padding: 0 12px;
        background: var(--app-header-background-color, var(--primary-color));
        overflow-x: auto;
      }
      .tab {
        border: none;
        border-bottom: 3px solid transparent;
        border-radius: 0;
        background: none;
        color: var(--app-header-text-color, var(--text-primary-color, #fff));
        opacity: 0.75;
        padding: 10px 14px;
        white-space: nowrap;
      }
      .tab.active {
        opacity: 1;
        border-bottom-color: var(--app-header-text-color, var(--text-primary-color, #fff));
      }
      .count {
        margin-left: 6px;
        font-size: 0.8em;
        opacity: 0.85;
      }
      .content {
        max-width: 1280px;
        margin: 0 auto;
        padding: 16px;
      }
    `],t([ut({attribute:!1})],ce.prototype,"narrow",void 0),t([ut({attribute:!1})],ce.prototype,"route",void 0),t([ut({attribute:!1})],ce.prototype,"panel",void 0),t([ft()],ce.prototype,"tab",void 0),t([ft()],ce.prototype,"interfaces",void 0),t([ft()],ce.prototype,"offline",void 0),t([ft()],ce.prototype,"periodic",void 0),t([ft()],ce.prototype,"activity",void 0),t([ft()],ce.prototype,"files",void 0),t([ft()],ce.prototype,"history",void 0),t([ft()],ce.prototype,"source",void 0),t([ft()],ce.prototype,"draft",void 0),t([ft()],ce.prototype,"confirmed",void 0),t([ft()],ce.prototype,"loaded",void 0),t([ft()],ce.prototype,"error",void 0),xt("woow-can-panel",ce);export{ce as WoowCanPanel};
