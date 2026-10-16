function t(t,e,i,s){var r,o=arguments.length,a=o<3?e:null===s?s=Object.getOwnPropertyDescriptor(e,i):s;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)a=Reflect.decorate(t,e,i,s);else for(var n=t.length-1;n>=0;n--)(r=t[n])&&(a=(o<3?r(a):o>3?r(e,i,a):r(e,i))||a);return o>3&&a&&Object.defineProperty(e,i,a),a}"function"==typeof SuppressedError&&SuppressedError;const e=globalThis,i=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s=Symbol(),r=new WeakMap;let o=class{constructor(t,e,i){if(this._$cssResult$=!0,i!==s)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const e=this.t;if(i&&void 0===t){const i=void 0!==e&&1===e.length;i&&(t=r.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),i&&r.set(e,t))}return t}toString(){return this.cssText}};const a=(t,...e)=>{const i=1===t.length?t[0]:e.reduce((e,i,s)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+t[s+1],t[0]);return new o(i,t,s)},n=i?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const i of t.cssRules)e+=i.cssText;return(t=>new o("string"==typeof t?t:t+"",void 0,s))(e)})(t):t,{is:c,defineProperty:d,getOwnPropertyDescriptor:l,getOwnPropertyNames:h,getOwnPropertySymbols:p,getPrototypeOf:u}=Object,m=globalThis,f=m.trustedTypes,v=f?f.emptyScript:"",_=m.reactiveElementPolyfillSupport,g=(t,e)=>t,b={toAttribute(t,e){switch(e){case Boolean:t=t?v:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let i=t;switch(e){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t)}catch(t){i=null}}return i}},$=(t,e)=>!c(t,e),y={attribute:!0,type:String,converter:b,reflect:!1,useDefault:!1,hasChanged:$};Symbol.metadata??=Symbol("metadata"),m.litPropertyMetadata??=new WeakMap;let w=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=y){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const i=Symbol(),s=this.getPropertyDescriptor(t,i,e);void 0!==s&&d(this.prototype,t,s)}}static getPropertyDescriptor(t,e,i){const{get:s,set:r}=l(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:s,set(e){const o=s?.call(this);r?.call(this,e),this.requestUpdate(t,o,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??y}static _$Ei(){if(this.hasOwnProperty(g("elementProperties")))return;const t=u(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(g("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(g("properties"))){const t=this.properties,e=[...h(t),...p(t)];for(const i of e)this.createProperty(i,t[i])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,i]of e)this.elementProperties.set(t,i)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const i=this._$Eu(t,e);void 0!==i&&this._$Eh.set(i,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const i=new Set(t.flat(1/0).reverse());for(const t of i)e.unshift(n(t))}else void 0!==t&&e.push(n(t));return e}static _$Eu(t,e){const i=e.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((t,s)=>{if(i)t.adoptedStyleSheets=s.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const i of s){const s=document.createElement("style"),r=e.litNonce;void 0!==r&&s.setAttribute("nonce",r),s.textContent=i.cssText,t.appendChild(s)}})(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){const i=this.constructor.elementProperties.get(t),s=this.constructor._$Eu(t,i);if(void 0!==s&&!0===i.reflect){const r=(void 0!==i.converter?.toAttribute?i.converter:b).toAttribute(e,i.type);this._$Em=t,null==r?this.removeAttribute(s):this.setAttribute(s,r),this._$Em=null}}_$AK(t,e){const i=this.constructor,s=i._$Eh.get(t);if(void 0!==s&&this._$Em!==s){const t=i.getPropertyOptions(s),r="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:b;this._$Em=s;const o=r.fromAttribute(e,t.type);this[s]=o??this._$Ej?.get(s)??o,this._$Em=null}}requestUpdate(t,e,i,s=!1,r){if(void 0!==t){const o=this.constructor;if(!1===s&&(r=this[t]),i??=o.getPropertyOptions(t),!((i.hasChanged??$)(r,e)||i.useDefault&&i.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,i))))return;this.C(t,e,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:s,wrapped:r},o){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),!0!==r||void 0!==o)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),!0===s&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,i]of t){const{wrapped:t}=i,s=this[e];!0!==t||this._$AL.has(e)||void 0===s||this.C(e,void 0,i,s)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};w.elementStyles=[],w.shadowRootOptions={mode:"open"},w[g("elementProperties")]=new Map,w[g("finalized")]=new Map,_?.({ReactiveElement:w}),(m.reactiveElementVersions??=[]).push("2.1.2");const x=globalThis,k=t=>t,A=x.trustedTypes,S=A?A.createPolicy("lit-html",{createHTML:t=>t}):void 0,E="$lit$",C=`lit$${Math.random().toFixed(9).slice(2)}$`,D="?"+C,I=`<${D}>`,N=document,M=()=>N.createComment(""),T=t=>null===t||"object"!=typeof t&&"function"!=typeof t,P=Array.isArray,O="[ \t\n\f\r]",R=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,U=/-->/g,z=/>/g,F=RegExp(`>|${O}(?:([^\\s"'>=/]+)(${O}*=${O}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),H=/'/g,B=/"/g,j=/^(?:script|style|textarea|title)$/i,L=t=>(e,...i)=>({_$litType$:t,strings:e,values:i}),W=L(1),q=L(2),V=Symbol.for("lit-noChange"),K=Symbol.for("lit-nothing"),J=new WeakMap,Z=N.createTreeWalker(N,129);function X(t,e){if(!P(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==S?S.createHTML(e):e}class G{constructor({strings:t,_$litType$:e},i){let s;this.parts=[];let r=0,o=0;const a=t.length-1,n=this.parts,[c,d]=((t,e)=>{const i=t.length-1,s=[];let r,o=2===e?"<svg>":3===e?"<math>":"",a=R;for(let e=0;e<i;e++){const i=t[e];let n,c,d=-1,l=0;for(;l<i.length&&(a.lastIndex=l,c=a.exec(i),null!==c);)l=a.lastIndex,a===R?"!--"===c[1]?a=U:void 0!==c[1]?a=z:void 0!==c[2]?(j.test(c[2])&&(r=RegExp("</"+c[2],"g")),a=F):void 0!==c[3]&&(a=F):a===F?">"===c[0]?(a=r??R,d=-1):void 0===c[1]?d=-2:(d=a.lastIndex-c[2].length,n=c[1],a=void 0===c[3]?F:'"'===c[3]?B:H):a===B||a===H?a=F:a===U||a===z?a=R:(a=F,r=void 0);const h=a===F&&t[e+1].startsWith("/>")?" ":"";o+=a===R?i+I:d>=0?(s.push(n),i.slice(0,d)+E+i.slice(d)+C+h):i+C+(-2===d?e:h)}return[X(t,o+(t[i]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),s]})(t,e);if(this.el=G.createElement(c,i),Z.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(s=Z.nextNode())&&n.length<a;){if(1===s.nodeType){if(s.hasAttributes())for(const t of s.getAttributeNames())if(t.endsWith(E)){const e=d[o++],i=s.getAttribute(t).split(C),a=/([.?@])?(.*)/.exec(e);n.push({type:1,index:r,name:a[2],strings:i,ctor:"."===a[1]?it:"?"===a[1]?st:"@"===a[1]?rt:et}),s.removeAttribute(t)}else t.startsWith(C)&&(n.push({type:6,index:r}),s.removeAttribute(t));if(j.test(s.tagName)){const t=s.textContent.split(C),e=t.length-1;if(e>0){s.textContent=A?A.emptyScript:"";for(let i=0;i<e;i++)s.append(t[i],M()),Z.nextNode(),n.push({type:2,index:++r});s.append(t[e],M())}}}else if(8===s.nodeType)if(s.data===D)n.push({type:2,index:r});else{let t=-1;for(;-1!==(t=s.data.indexOf(C,t+1));)n.push({type:7,index:r}),t+=C.length-1}r++}}static createElement(t,e){const i=N.createElement("template");return i.innerHTML=t,i}}function Q(t,e,i=t,s){if(e===V)return e;let r=void 0!==s?i._$Co?.[s]:i._$Cl;const o=T(e)?void 0:e._$litDirective$;return r?.constructor!==o&&(r?._$AO?.(!1),void 0===o?r=void 0:(r=new o(t),r._$AT(t,i,s)),void 0!==s?(i._$Co??=[])[s]=r:i._$Cl=r),void 0!==r&&(e=Q(t,r._$AS(t,e.values),r,s)),e}class Y{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:i}=this._$AD,s=(t?.creationScope??N).importNode(e,!0);Z.currentNode=s;let r=Z.nextNode(),o=0,a=0,n=i[0];for(;void 0!==n;){if(o===n.index){let e;2===n.type?e=new tt(r,r.nextSibling,this,t):1===n.type?e=new n.ctor(r,n.name,n.strings,this,t):6===n.type&&(e=new ot(r,this,t)),this._$AV.push(e),n=i[++a]}o!==n?.index&&(r=Z.nextNode(),o++)}return Z.currentNode=N,s}p(t){let e=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}}class tt{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,i,s){this.type=2,this._$AH=K,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=Q(this,t,e),T(t)?t===K||null==t||""===t?(this._$AH!==K&&this._$AR(),this._$AH=K):t!==this._$AH&&t!==V&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>P(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==K&&T(this._$AH)?this._$AA.nextSibling.data=t:this.T(N.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:i}=t,s="number"==typeof i?this._$AC(t):(void 0===i.el&&(i.el=G.createElement(X(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===s)this._$AH.p(e);else{const t=new Y(s,this),i=t.u(this.options);t.p(e),this.T(i),this._$AH=t}}_$AC(t){let e=J.get(t.strings);return void 0===e&&J.set(t.strings,e=new G(t)),e}k(t){P(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let i,s=0;for(const r of t)s===e.length?e.push(i=new tt(this.O(M()),this.O(M()),this,this.options)):i=e[s],i._$AI(r),s++;s<e.length&&(this._$AR(i&&i._$AB.nextSibling,s),e.length=s)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=k(t).nextSibling;k(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class et{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,s,r){this.type=1,this._$AH=K,this._$AN=void 0,this.element=t,this.name=e,this._$AM=s,this.options=r,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=K}_$AI(t,e=this,i,s){const r=this.strings;let o=!1;if(void 0===r)t=Q(this,t,e,0),o=!T(t)||t!==this._$AH&&t!==V,o&&(this._$AH=t);else{const s=t;let a,n;for(t=r[0],a=0;a<r.length-1;a++)n=Q(this,s[i+a],e,a),n===V&&(n=this._$AH[a]),o||=!T(n)||n!==this._$AH[a],n===K?t=K:t!==K&&(t+=(n??"")+r[a+1]),this._$AH[a]=n}o&&!s&&this.j(t)}j(t){t===K?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class it extends et{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===K?void 0:t}}class st extends et{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==K)}}class rt extends et{constructor(t,e,i,s,r){super(t,e,i,s,r),this.type=5}_$AI(t,e=this){if((t=Q(this,t,e,0)??K)===V)return;const i=this._$AH,s=t===K&&i!==K||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,r=t!==K&&(i===K||s);s&&this.element.removeEventListener(this.name,this,i),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class ot{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){Q(this,t)}}const at={I:tt},nt=x.litHtmlPolyfillSupport;nt?.(G,tt),(x.litHtmlVersions??=[]).push("3.3.3");const ct=globalThis;let dt=class extends w{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,i)=>{const s=i?.renderBefore??e;let r=s._$litPart$;if(void 0===r){const t=i?.renderBefore??null;s._$litPart$=r=new tt(e.insertBefore(M(),t),t,void 0,i??{})}return r._$AI(t),r})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return V}};dt._$litElement$=!0,dt.finalized=!0,ct.litElementHydrateSupport?.({LitElement:dt});const lt=ct.litElementPolyfillSupport;lt?.({LitElement:dt}),(ct.litElementVersions??=[]).push("4.2.2");const ht={attribute:!0,type:String,converter:b,reflect:!1,hasChanged:$},pt=(t=ht,e,i)=>{const{kind:s,metadata:r}=i;let o=globalThis.litPropertyMetadata.get(r);if(void 0===o&&globalThis.litPropertyMetadata.set(r,o=new Map),"setter"===s&&((t=Object.create(t)).wrapped=!0),o.set(i.name,t),"accessor"===s){const{name:s}=i;return{set(i){const r=e.get.call(this);e.set.call(this,i),this.requestUpdate(s,r,t,!0,i)},init(e){return void 0!==e&&this.C(s,void 0,t,e),e}}}if("setter"===s){const{name:s}=i;return function(i){const r=this[s];e.call(this,i),this.requestUpdate(s,r,t,!0,i)}}throw Error("Unsupported decorator location: "+s)};function ut(t){return(e,i)=>"object"==typeof i?pt(t,e,i):((t,e,i)=>{const s=e.hasOwnProperty(i);return e.constructor.createProperty(i,t),s?Object.getOwnPropertyDescriptor(e,i):void 0})(t,e,i)}function mt(t){return ut({...t,state:!0,attribute:!1})}const ft=2**32;function vt(t){return Math.floor(t/2147483648)%2==1}function _t(t){const e=t%536870912;return vt(t)?e.toString(16).toUpperCase().padStart(8,"0"):(e%2048).toString(16).toUpperCase().padStart(3,"0")}function gt(t,e,i){if(16&e)return`${(536870912+t%536870912).toString(16).toUpperCase().padStart(8,"0")}#${i}`;const s=_t(t);return!function(t){return Math.floor(t/1073741824)%2==1}(t)||1&e?1&e?`${s}##${2&e?1:0}${i}`:`${s}#${i}`:`${s}#R`}class bt{constructor(t){this.exact=new Set,this.masks=[],this.ranges=[],this.error="";let e=!t.trim(),i="";for(const s of t.split(/[,;]/)){const t=s.trim();if(t)if("*"!==t)try{if(t.includes("-")){const[e,i]=t.split("-"),[s,r]=$t(e),[o,a]=$t(i);if(o<s)throw new Error(t);this.ranges.push([s,o,r||a])}else if(t.includes("/")){const[e,i]=t.split("/"),[s,r]=$t(e);this.masks.push([s,$t(i)[0],r])}else{const[e,i]=$t(t);this.exact.add(`${i?"x":""}${e}`)}}catch{i=t}else e=!0}this.all=e,this.error=i}matches(t){if(this.all)return!0;const e=vt(t),i=e?t%536870912:t%2048;if(this.exact.has(`${e?"x":""}${i}`))return!0;for(const[t,s,r]of this.masks)if(r===e&&(i&s)===(t&s))return!0;for(const[t,s,r]of this.ranges)if(r===e&&i>=t&&i<=s)return!0;return!1}}function $t(t){let e=t.trim();if(e.toLowerCase().startsWith("0x")&&(e=e.slice(2)),!/^[0-9a-fA-F]{1,8}$/.test(e))throw new Error(`bad CAN ID ${t}`);const i=parseInt(e,16);if(i>536870911)throw new Error(`CAN ID ${t} is out of range`);return[i,e.length>3||i>2047]}class yt{constructor(t){this.hass=t}subscribe(t){return this.hass().connection.subscribeMessage(t,{type:"woow_can/subscribe"})}snapshot(){return this.hass().callWS({type:"woow_can/snapshot"})}subscribeMonitor(t,e,i){return this.hass().connection.subscribeMessage(i,{type:"woow_can/monitor/subscribe",source:t,token:e})}ack(t,e){return this.hass().callWS({type:"woow_can/monitor/ack",token:t,seq:e})}clearMonitor(t){return this.hass().callWS({type:"woow_can/monitor/clear",source:t})}trace(t,e){return this.hass().callWS({type:"woow_can/trace",source:t,limit:e.limit??200,ids:e.ids??"",...null!=e.before?{before:e.before}:{},...e.direction?{direction:e.direction}:{}})}send(t,e,i=0,s=""){return this.hass().callWS({type:"woow_can/send",entry_id:t,frame:e,wait_ms:i,...s?{wait_id:s}:{}})}setEvents(t,e){return this.hass().callWS({type:"woow_can/interface/events",entry_id:t,event_filter:e})}savePeriodic(t){return this.hass().callWS({type:"woow_can/periodic/save",item:t})}controlPeriodic(t,e){return this.hass().callWS({type:"woow_can/periodic/control",item_id:t,action:e})}captures(){return this.hass().callWS({type:"woow_can/capture/list"})}capture(t,e){return this.hass().callWS({type:"woow_can/capture/control",action:t,...e})}saveDevice(t){return this.hass().callWS({type:"woow_can/devices/save",device:t})}deleteDevice(t){return this.hass().callWS({type:"woow_can/devices/delete",device_id:t})}setSignal(t,e,i,s){return this.hass().callWS({type:"woow_can/devices/signal",device_id:t,message:e,signal:i,...s})}createFromTemplate(t,e,i,s,r){return this.hass().callWS({type:"woow_can/templates/create",template:t,entry_id:e,name:i,params:s,groups:r})}decode(t,e,i){return this.hass().callWS({type:"woow_can/decode",source:t,raw:e,data:i})}dbc(t,e,i={}){return this.hass().callWS({type:"woow_can/dbc/control",action:t,name:e,...i})}async uploadDbc(t,e){const i=`name=${encodeURIComponent(t.name)}${e.length?`&attach=${encodeURIComponent(e.join(","))}`:""}`,s=await this.hass().fetchWithAuth(`/api/woow_can/dbc?${i}`,{method:"POST",body:t});if(!s.ok)throw new Error(`${s.status} ${await s.text()}`);return await s.json()}async download(t){const e=await this.hass().callWS({type:"auth/sign_path",path:t,expires:60}),i=document.createElement("a");i.href=this.hass().hassUrl(e.path),i.download="",document.body.appendChild(i),i.click(),i.remove()}async upload(t){const e=await this.hass().fetchWithAuth(`/api/woow_can/captures?name=${encodeURIComponent(t.name)}`,{method:"POST",body:t});if(!e.ok)throw new Error(`${e.status} ${await e.text()}`);return(await e.json()).name}}function wt(t){return String(t&&"object"==typeof t&&"message"in t?t.message:t)}function xt(t,e){customElements.get(t)||customElements.define(t,e)}function kt(t,e){try{const i=window.localStorage.getItem(t);return i?JSON.parse(i):e}catch{return e}}function At(t,e){try{window.localStorage.setItem(t,JSON.stringify(e))}catch{}}const St={title:"WOOW CAN",tab_overview:"Overview",tab_monitor:"Monitor",tab_send:"Send",tab_capture:"Recordings",tab_activity:"Activity",loading:"Loading…",error:"Error: {msg}",cancel:"Cancel",close:"Close",save:"Save",delete:"Delete",edit:"Edit",add:"Add",start:"Start",stop:"Stop",none:"none",just_now:"just now",s_ago:"{n} s ago",m_ago:"{n} min ago",h_ago:"{n} h ago",d_ago:"{n} d ago",no_interfaces:"No CAN interfaces yet. Add one under Settings › Devices & services › WOOW CAN; without hardware, add a virtual interface to try things out.",state_error_active:"Normal",state_error_warning:"Error warning",state_error_passive:"Error passive",state_bus_off:"Bus off",state_stopped:"Stopped",state_sleeping:"Sleeping",state_virtual:"Virtual",state_unknown:"Unknown",unavailable:"Unavailable",listen_only:"listen only",can_fd:"CAN FD",kbps:"{n} kbit/s",virtual_iface:"virtual",load:"Bus load",load_values:"now {now} · peak {peak} · 1/5/15 min {a1} / {a5} / {a15}",load_hint:"Estimated with worst-case bit stuffing; it can exceed 100 %.",rates:"received {rx}/s · sent {tx}/s",traffic:"Traffic",seen:"Seen since start",tec_rec:"TEC / REC",controller_events:"Warnings / passive / bus-off / restarts",bus_errors:"Bus errors",arbitration_lost:"Arbitration lost",not_supported:"not reported by this controller",reporting_off:"reporting off",drops:"Dropped (socket / controller overflow / over the event rate)",last_error:"Last error frame",ids_seen:"{n} IDs · {f} frames",recording_now:"Recording {name} ({n} frames)",clock_mhz:"clock {n} MHz",sample_point:"sample point {n} %",events_filter:"Events for: {x}",events_none:"No events (event filter empty)",open_monitor:"Monitor",hint_passive:"Nothing on the bus acknowledges this interface's frames. Check the wiring, the 120 Ω termination at both ends and that every node uses the same bitrate.",hint_bus_off_auto:"The controller went bus-off; it restarts after {ms} ms.",hint_bus_off_manual:"The controller went bus-off and stays off: reload the interface.",hint_listen_only:"Listen only: this interface never acknowledges or sends.",hint_overflow:"The controller lost {n} frames (receive overflow): the bus is busier than it can follow.",hint_socket_drops:"{n} frames were dropped before Home Assistant read them.",sparkline:"Load over the last minutes","err_controller:rx_overflow":"receive overflow","err_controller:tx_overflow":"transmit overflow","err_controller:rx_warning":"receive errors at warning level","err_controller:tx_warning":"transmit errors at warning level","err_controller:rx_passive":"receive error passive","err_controller:tx_passive":"transmit error passive","err_controller:active":"back to error active",err_controller:"controller problem","err_protocol:bit":"bit error","err_protocol:form":"form error","err_protocol:stuff":"stuff error","err_protocol:bit0":"could not send a dominant bit","err_protocol:bit1":"could not send a recessive bit","err_protocol:overload":"bus overload","err_protocol:active_error":"active error flag","err_protocol:on_tx":"while transmitting",err_protocol:"protocol error",err_tx_timeout:"transmit timeout",err_lost_arbitration:"lost arbitration",err_transceiver:"transceiver problem",err_no_ack:"no acknowledgement",err_bus_off:"bus off",err_bus_error:"bus error",err_restarted:"controller restarted",source:"Source",file_source:"{name} (file)",pause:"Pause",resume:"Resume",clear:"Clear",notch:"Notch",notch_clear:"Clear notch",changing_only:"Changing only",hide_inactive:"Hide silent > 5 s",view_hex:"HEX",view_bin:"Binary",filter_ph:"IDs: 123, 7E0/7F0, 100-1FF",filter_bad:"Not understood: {x}",col_id:"ID",col_name:"Name",col_len:"Len",col_data:"Data",col_count:"Count",col_hz:"Hz",col_period:"Period",col_dchg:"Change gap",col_age:"Age",col_time:"Time",col_dir:"Dir",dir_rx:"Rx",dir_tx:"Tx",dir_local:"this host",monitor_empty:"No frames yet. Check that the bus is connected and every node uses the same bitrate, or open a recording under Recordings.",monitor_hint:"One row per ID. A changed byte lights up and fades: cyan rising, red falling, grey-violet for bytes that keep jumping (counters, checksums). To find a signal: leave the equipment alone for 10 s, press Notch two or three times until the screen is quiet, then operate the equipment and watch which bytes light up.",notch_added:"Masked {n} bits that changed in the last 2 s.",notch_none:"No bits changed in the last 2 s.",overflow:"More than 4096 IDs: {n} further frames are only counted.",frames_total:"{ids} IDs · {n} frames",row_pin:"Pin",row_unpin:"Unpin",row_send:"Send again",row_events:"Fire events",row_events_on:"Fires events",row_trace:"In time order",row_notch:"Notch this row",detail_period:"Period {avg} ms ({min}–{max})",detail_rate:"{hz} frames/s",detail_changed:"Data last changed {ago}; gap between the last two changes {gap}",paused_title:"Paused: frames in time order, newest first",trace_older:"Older",trace_start:"That is the oldest frame in the buffer.",trace_all_dirs:"Both directions",trace_time:"Time",trace_delta:"Δ",trace_error:"error frame: {x}",trace_empty:"No frames match.",events_added:"Frames with ID {id} now fire woow_can_frame events.",gone:"The interface was reloaded; reconnecting…",offline_note:"Recording {file}: {n} frames. The monitor shows the state at the end of the file.",send_title:"Send a frame",interface:"Interface",frame:"Frame",frame_ph:"123#11223344",frame_help:"ID#data: 1–3 digit IDs are 11-bit, longer ones 29-bit; 123#R is a remote frame; ID##1data is CAN FD (1 = bit rate switch).",wait_id:"Reply ID",wait_ms:"Wait (ms)",send:"Send",sent_ok:"Sent {frame}",reply:"Reply {frame}",no_reply:"No reply (timed out)",cannot_send:"{name} cannot send: {why}",why_listen:"it is set to listen only (turn that off in the interface settings)",why_unavailable:"it is not available",confirm_title:"First send on {name}",confirm_text:"Every node on the bus receives this frame. On a vehicle, machine or battery bus, only send frames whose effect you know.",confirm_ok:"Send",periodic_title:"Periodic sends",periodic_hint:"Frames sent every N ms. After Home Assistant restarts every item is stopped.",name:"Name",period_ms:"Period (ms)",count:"Count (0 = no limit)",running:"running",stopped:"stopped",sent_n:"{n} sent",stopped_by_count:"count reached",stopped_by_error:"stopped: {x}",stopped_by_interface:"interface stopped",periodic_empty:"No periodic sends yet.",capture_title:"Record",capture_hint:"Record an interface to a candump log file (canplayer, SavvyCAN, python-can and Wireshark read it), kept in Home Assistant's config folder under woow_can/captures.",record:"Record",stop_record:"Stop",recording:"Recording · {n} frames · {size}",export:"Download buffer",export_hint:"The last {n} frames held in memory, as a candump log.",files_title:"Recordings",files_empty:"No recordings yet.",download:"Download",open:"Open",upload:"Upload a log file",uploaded:"Uploaded {name}.",opened:"Opened; pick it as the source on the Monitor tab.",offline_title:"Open files",truncated:"only the last {n} frames",delete_confirm:"Delete {name}?",all_channels:"All sources",channel_service:"Service / AI",channel_panel:"Panel",channel_entity:"Entity",activity_hint:"Sends and changes made by AI agents (through services) and by people (in this panel).",activity_empty:"Nothing yet.",quoted:"“{x}”",log_sent:"sent {frame} on {port}",log_send_failed:"sending {frame} on {port} failed: {error}",log_periodic_saved:"saved periodic send “{name}”: {frame} every {period} ms on {port}",log_periodic_deleted:"deleted periodic send “{name}”",log_periodic_started:"started periodic send “{name}” on {port}",log_periodic_stopped:"stopped periodic send “{name}” ({sent} sent)",log_periodic_failed:"periodic send “{name}” stopped: {error}",log_capture_started:"started recording {file} on {port}",log_capture_stopped:"stopped recording {file} ({frames} frames)",log_capture_deleted:"deleted recording {file}",log_capture_uploaded:"uploaded {file}",log_monitor_cleared:"cleared the monitor of {port}",tab_devices:"Devices",devices_hint:"A device turns chosen signals of an interface into Home Assistant entities. Start from a template for known equipment, or from an imported DBC file.",devices_empty:"No devices yet. Add one from a template, or import a DBC file.",add_from_template:"From a template",import_dbc:"Import DBC",template:"Template",category_battery:"Battery",category_vehicle:"Vehicle",category_marine:"Marine",category_industrial:"Industrial",confidence:"Confidence: {x}",confidence_high:"high",confidence_medium:"medium",confidence_low:"low",verified_with:"Checked against: {x}",sources:"Sources",license_x:"License: {x}",only_listens:"Only listens, never sends",groups_title:"Message groups",groups_auto:"Detect from traffic",groups_detect_hint:"Groups whose IDs this interface has already received are included.",device_name:"Device name",create:"Create",created_device:"Created {name}.",messages_n:"{n} messages",entities_n:"{n} entities",never_seen:"never received",stale:"silent",fresh:"receiving",col_signal:"Signal",col_value:"Value",col_entity:"Entity",adopt_hint:"Checked signals are Home Assistant entities.",state_on:"on",state_off:"off",entity_disabled:"disabled",settings:"Settings",min_interval:"Minimum interval (s)",tolerance:"Tolerance",timeout_s:"Timeout (s)",apply:"Apply",delete_device_confirm:"Delete {name} and its entities?",from_x:"from {x}",chart:"Chart",charts_title:"Charts",charts_empty:"Press Chart next to a numeric signal to follow it here.",dbc_title:"DBC files",dbc_hint:"Attached to an interface, a DBC file names and decodes the monitor's rows. To get entities, make a device from some of its messages.",dbc_empty:"No DBC files yet.",dbc_attached_to:"Decodes",all_interfaces:"All interfaces",dbc_warnings:"{n} lines not understood",make_device:"Make a device",download_dbc:"Download as DBC",choose_messages:"Messages",imported_dbc:"Imported {name}: {m} messages, {s} signals.",decoded_title:"Decoded",no_definition:"No device or DBC file describes this ID.",log_device_created:"created device “{device}” on {port}",log_device_updated:"updated device “{device}” on {port}",log_device_from_template:"created device “{device}” from template {template} on {port}",log_device_from_dbc:"created device “{device}” from {file} on {port}",log_device_deleted:"deleted device “{device}”",log_device_save_failed:"could not save device “{device}”: {error}",log_signal_changed:"{device}: changed signal {signal}",log_dbc_imported:"imported {file} ({messages} messages)",log_dbc_attached:"{file} decodes {ports}",log_dbc_deleted:"deleted {file}"},Et={title:"WOOW CAN",tab_overview:"總覽",tab_monitor:"監看",tab_send:"發送",tab_capture:"擷取",tab_activity:"活動",loading:"載入中…",error:"錯誤：{msg}",cancel:"取消",close:"關閉",save:"儲存",delete:"刪除",edit:"編輯",add:"新增",start:"開始",stop:"停止",none:"無",just_now:"剛剛",s_ago:"{n} 秒前",m_ago:"{n} 分鐘前",h_ago:"{n} 小時前",d_ago:"{n} 天前",no_interfaces:"還沒有 CAN 介面。請到「設定 › 裝置與服務 › WOOW CAN」新增；沒有硬體的話，可以新增虛擬介面先試用。",state_error_active:"正常",state_error_warning:"錯誤警告",state_error_passive:"錯誤被動",state_bus_off:"Bus off（已離線）",state_stopped:"已停止",state_sleeping:"休眠",state_virtual:"虛擬介面",state_unknown:"未知",unavailable:"無法使用",listen_only:"只監聽",can_fd:"CAN FD",kbps:"{n} kbit/s",virtual_iface:"虛擬",load:"匯流排負載",load_values:"目前 {now} · 峰值 {peak} · 1／5／15 分鐘 {a1}／{a5}／{a15}",load_hint:"以最壞位元填充估算，所以可能超過 100%。",rates:"收 {rx} 筆/秒 · 送 {tx} 筆/秒",traffic:"流量",seen:"啟動以來",tec_rec:"TEC／REC",controller_events:"錯誤警告／錯誤被動／Bus off／重啟",bus_errors:"匯流排錯誤",arbitration_lost:"仲裁失敗",not_supported:"這顆控制器不回報",reporting_off:"未開啟回報",drops:"丟包（socket／控制器溢位／超過事件速率）",last_error:"最後一筆錯誤訊框",ids_seen:"{n} 個 ID · {f} 筆",recording_now:"錄製中：{name}（{n} 筆）",clock_mhz:"時脈 {n} MHz",sample_point:"取樣點 {n}%",events_filter:"觸發事件：{x}",events_none:"不觸發事件（事件 ID 空白）",open_monitor:"監看",hint_passive:"送出的訊框沒有任何節點回應確認（ACK）。請檢查接線、兩端的 120 Ω 終端電阻，以及所有節點的速率是否一致。",hint_bus_off_auto:"控制器進入 bus off，{ms} ms 後會自動重啟。",hint_bus_off_manual:"控制器進入 bus off，不會自動恢復：請重新載入這個介面。",hint_listen_only:"只監聽：這個介面不回 ACK，也不能發送。",hint_overflow:"控制器漏收了 {n} 筆（接收溢位）：匯流排比它能處理的還忙。",hint_socket_drops:"有 {n} 筆在 Home Assistant 讀取前就被丟掉了。",sparkline:"最近幾分鐘的負載","err_controller:rx_overflow":"接收溢位","err_controller:tx_overflow":"發送溢位","err_controller:rx_warning":"接收錯誤達警告","err_controller:tx_warning":"發送錯誤達警告","err_controller:rx_passive":"接收錯誤被動","err_controller:tx_passive":"發送錯誤被動","err_controller:active":"恢復正常",err_controller:"控制器問題","err_protocol:bit":"位元錯誤","err_protocol:form":"格式錯誤","err_protocol:stuff":"填充錯誤","err_protocol:bit0":"送不出顯性位元","err_protocol:bit1":"送不出隱性位元","err_protocol:overload":"匯流排過載","err_protocol:active_error":"主動錯誤旗標","err_protocol:on_tx":"發送時發生",err_protocol:"協定錯誤",err_tx_timeout:"發送逾時",err_lost_arbitration:"仲裁失敗",err_transceiver:"收發器問題",err_no_ack:"沒有人回 ACK",err_bus_off:"Bus off",err_bus_error:"匯流排錯誤",err_restarted:"控制器已重啟",source:"來源",file_source:"{name}（檔案）",pause:"暫停",resume:"繼續",clear:"清除",notch:"Notch",notch_clear:"清除 Notch",changing_only:"只看在變",hide_inactive:"隱藏 5 秒沒收到的",view_hex:"HEX",view_bin:"二進位",filter_ph:"篩選 ID：123, 7E0/7F0, 100-1FF",filter_bad:"看不懂：{x}",col_id:"ID",col_name:"名稱",col_len:"長度",col_data:"資料",col_count:"次數",col_hz:"Hz",col_period:"週期",col_dchg:"變化間隔",col_age:"距今",col_time:"時間",col_dir:"方向",dir_rx:"收",dir_tx:"送",dir_local:"本機",monitor_empty:"還沒收到任何訊框。請確認匯流排有接上、所有節點速率一致；或到「擷取」分頁開啟一個紀錄檔。",monitor_hint:"每個 ID 一列。數值變了會上色再慢慢淡掉：上升青、下降紅，一直在跳的（計數器、校驗碼）用灰紫。找訊號的方法：先不要操作 10 秒，按 Notch 兩三次直到畫面安靜，再操作設備，看哪幾格亮起來。",notch_added:"已遮掉 {n} 個最近 2 秒內變過的位元。",notch_none:"最近 2 秒沒有位元變動。",overflow:"ID 超過 4096 個，另外 {n} 筆只計數。",frames_total:"{ids} 個 ID · 共 {n} 筆",row_pin:"釘選",row_unpin:"取消釘選",row_send:"再送一次",row_events:"觸發事件",row_events_on:"已觸發事件",row_trace:"看時間序",row_notch:"遮掉這列",detail_period:"週期 {avg} ms（{min}–{max}）",detail_rate:"每秒 {hz} 筆",detail_changed:"資料最後變化：{ago}；最近兩次變化間隔 {gap}",paused_title:"已暫停：依時間排列（新的在前）",trace_older:"更早",trace_start:"已經是緩衝區裡最舊的一筆。",trace_all_dirs:"收送都看",trace_time:"時間",trace_delta:"間隔",trace_error:"錯誤訊框：{x}",trace_empty:"沒有符合的訊框。",events_added:"ID {id} 收到時，會觸發 woow_can_frame 事件。",gone:"介面重新載入了，正在重新連線…",offline_note:"紀錄檔 {file}：{n} 筆。監看顯示的是檔案結尾時的狀態。",send_title:"發送訊框",interface:"介面",frame:"訊框",frame_ph:"123#11223344",frame_help:"寫法：ID#資料。1–3 位數的 ID＝11-bit，更長＝29-bit；123#R＝遠端訊框；ID##1資料＝CAN FD（1＝切換速率）。",wait_id:"等回覆 ID",wait_ms:"等待（ms）",send:"送出",sent_ok:"已送出 {frame}",reply:"回覆 {frame}",no_reply:"沒有回覆（逾時）",cannot_send:"{name} 不能發送：{why}",why_listen:"設定為只監聽（到介面設定關閉）",why_unavailable:"目前無法使用",confirm_title:"第一次從 {name} 發送",confirm_text:"匯流排上的所有節點都會收到這筆訊框。如果是車輛、機器或電池的匯流排，請只送你清楚作用的訊框。",confirm_ok:"確定送出",periodic_title:"週期發送",periodic_hint:"每隔 N ms 送一次。Home Assistant 重新啟動後，所有項目都會先停止。",name:"名稱",period_ms:"週期（ms）",count:"次數（0＝不限）",running:"執行中",stopped:"已停止",sent_n:"已送 {n} 筆",stopped_by_count:"已送滿次數",stopped_by_error:"出錯停止：{x}",stopped_by_interface:"介面停止",periodic_empty:"還沒有週期發送。",capture_title:"錄製",capture_hint:"把介面的訊框錄成 candump 紀錄檔（canplayer、SavvyCAN、python-can、Wireshark 都能讀），存在 Home Assistant 設定資料夾的 woow_can/captures。",record:"開始錄製",stop_record:"停止",recording:"錄製中 · {n} 筆 · {size}",export:"下載緩衝區",export_hint:"記憶體裡最近的 {n} 筆，存成 candump 紀錄檔。",files_title:"擷取檔",files_empty:"還沒有擷取檔。",download:"下載",open:"開啟",upload:"上傳紀錄檔",uploaded:"已上傳 {name}。",opened:"已開啟；到「監看」分頁把來源切到這個檔案。",offline_title:"已開啟的檔案",truncated:"只載入最後 {n} 筆",delete_confirm:"刪除 {name}？",all_channels:"全部來源",channel_service:"服務／AI",channel_panel:"面板",channel_entity:"實體",activity_hint:"AI（透過服務）和人（在這個面板）做的發送與變更，都記在這裡。",activity_empty:"還沒有紀錄。",quoted:"「{x}」",log_sent:"從 {port} 送出 {frame}",log_send_failed:"從 {port} 送出 {frame} 失敗：{error}",log_periodic_saved:"儲存週期發送「{name}」：{frame}，每 {period} ms，{port}",log_periodic_deleted:"刪除週期發送「{name}」",log_periodic_started:"開始週期發送「{name}」（{port}）",log_periodic_stopped:"停止週期發送「{name}」（已送 {sent} 筆）",log_periodic_failed:"週期發送「{name}」出錯停止：{error}",log_capture_started:"開始錄製 {file}（{port}）",log_capture_stopped:"停止錄製 {file}（{frames} 筆）",log_capture_deleted:"刪除擷取檔 {file}",log_capture_uploaded:"上傳擷取檔 {file}",log_monitor_cleared:"清除 {port} 的監看",tab_devices:"裝置",devices_hint:"裝置會把介面上選定的訊號變成 Home Assistant 實體。已知的設備從範本開始，也可以從匯入的 DBC 檔建立。",devices_empty:"還沒有裝置。從範本新增，或匯入 DBC 檔。",add_from_template:"從範本新增",import_dbc:"匯入 DBC",template:"範本",category_battery:"電池",category_vehicle:"車輛",category_marine:"船舶",category_industrial:"工業",confidence:"可信度：{x}",confidence_high:"高",confidence_medium:"中",confidence_low:"低",verified_with:"驗證依據：{x}",sources:"出處",license_x:"授權：{x}",only_listens:"只監聽，不會發送",groups_title:"訊息群組",groups_auto:"依實際流量判斷",groups_detect_hint:"會納入這個介面上已經收到過的群組。",device_name:"裝置名稱",create:"建立",created_device:"已建立 {name}。",messages_n:"{n} 則訊息",entities_n:"{n} 個實體",never_seen:"還沒收到",stale:"停止傳送",fresh:"持續收到",col_signal:"訊號",col_value:"數值",col_entity:"實體",adopt_hint:"勾選的訊號會成為 Home Assistant 實體。",state_on:"開",state_off:"關",entity_disabled:"停用中",settings:"設定",min_interval:"最短更新間隔（秒）",tolerance:"容差",timeout_s:"逾時（秒）",apply:"套用",delete_device_confirm:"刪除 {name} 和它的實體？",from_x:"來源：{x}",chart:"曲線",charts_title:"即時曲線",charts_empty:"在數值訊號旁按「曲線」，就會在這裡畫出來。",dbc_title:"DBC 檔",dbc_hint:"DBC 檔附加到介面後，監看會用它命名和解碼訊框；要變成實體，就從裡面挑訊息建立裝置。",dbc_empty:"還沒有 DBC 檔。",dbc_attached_to:"解碼介面",all_interfaces:"全部介面",dbc_warnings:"{n} 行看不懂",make_device:"建立裝置",download_dbc:"下載成 DBC",choose_messages:"訊息",imported_dbc:"已匯入 {name}：{m} 則訊息、{s} 個訊號。",decoded_title:"解碼",no_definition:"沒有裝置或 DBC 檔定義這個 ID。",log_device_created:"在 {port} 建立裝置「{device}」",log_device_updated:"修改裝置「{device}」（{port}）",log_device_from_template:"用範本 {template} 在 {port} 建立裝置「{device}」",log_device_from_dbc:"用 {file} 在 {port} 建立裝置「{device}」",log_device_deleted:"刪除裝置「{device}」",log_device_save_failed:"裝置「{device}」存不了：{error}",log_signal_changed:"{device}：修改訊號 {signal}",log_dbc_imported:"匯入 {file}（{messages} 則訊息）",log_dbc_attached:"{file} 解碼 {ports}",log_dbc_deleted:"刪除 {file}"};function Ct(t){const e=t.toLowerCase().startsWith("zh")?Et:St;return(t,i)=>{let s=e[t]??St[t]??t;if(i)for(const[t,e]of Object.entries(i))s=s.split(`{${t}}`).join(String(e));return s}}function Dt(t){return t in St}function It(t,e,i=Date.now()/1e3){const s=Math.max(0,i-t);return s<5?e("just_now"):s<60?e("s_ago",{n:Math.floor(s)}):s<3600?e("m_ago",{n:Math.floor(s/60)}):s<86400?e("h_ago",{n:Math.floor(s/3600)}):e("d_ago",{n:Math.floor(s/86400)})}function Nt(t){const e=new Date(1e3*t),i=(t,e=2)=>String(t).padStart(e,"0");return`${i(e.getHours())}:${i(e.getMinutes())}:${i(e.getSeconds())}.${i(e.getMilliseconds(),3)}`}function Mt(t){return null!=t&&isFinite(t)?t<1?`${(1e3*t).toFixed(t<.01?2:1)} ms`:t<100?`${t.toFixed(2)} s`:`${Math.round(t)} s`:"–"}function Tt(t){return t<1024?`${t} B`:t<1048576?`${(t/1024).toFixed(1)} KB`:`${(t/1024/1024).toFixed(1)} MB`}function Pt(t){return null==t?"–":`${t.toFixed(t<10?1:0)}%`}const Ot=a`
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
`,Rt=a`
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
`;class Ut extends dt{constructor(){super(...arguments),this.entries=[],this.now=0,this.channel=""}channelLabel(t){const e=`channel_${t}`;return Dt(e)?this.t(e):t}message(t){const e=`log_${t.msg}`;return t.msg&&Dt(e)?this.t(e,{...t.args??{}}):t.summary}render(){const t=this.t,e=this.entries.filter(t=>!this.channel||t.channel===this.channel).sort((t,e)=>e.t-t.t);return W`<div class="card">
      <div class="row">
        <h2 class="grow">${t("tab_activity")}</h2>
        <select @change=${t=>this.channel=(t=>t.target.value)(t)}>
          <option value="">${t("all_channels")}</option>
          ${["service","panel","entity"].map(t=>W`<option value=${t}>${this.channelLabel(t)}</option>`)}
        </select>
      </div>
      <div class="muted">${t("activity_hint")}</div>
      ${0===e.length?W`<div class="empty">${t("activity_empty")}</div>`:e.map(e=>W`<div class="entry">
              <div class="when" title=${new Date(1e3*e.t).toLocaleString()}>${It(e.t,t)}<br />${Nt(e.t).slice(0,8)}</div>
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
    </div>`}}Ut.styles=[Ot,a`
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
    `],t([ut({attribute:!1})],Ut.prototype,"entries",void 0),t([ut({attribute:!1})],Ut.prototype,"now",void 0),t([ut({attribute:!1})],Ut.prototype,"t",void 0),t([ut({attribute:!1})],Ut.prototype,"portName",void 0),t([mt()],Ut.prototype,"channel",void 0),xt("woow-can-activity",Ut);class zt extends dt{constructor(){super(...arguments),this.interfaces=[],this.offline=[],this.files=[],this.message=null,this.deleting="",this.busy=!1}async run(t,e){this.busy=!0;try{await t(),this.message=e?{ok:!0,text:e}:null}catch(t){this.message={ok:!1,text:this.t("error",{msg:wt(t)})}}finally{this.busy=!1}}changed(){this.dispatchEvent(new CustomEvent("captures-changed"))}async upload(t){const e=t.target,i=e.files?.[0];e.value="",i&&await this.run(async()=>{const t=await this.api.upload(i);this.message={ok:!0,text:this.t("uploaded",{name:t})},this.changed()})}async open(t){await this.run(async()=>{const e=await this.api.capture("open",{name:t}),i=e.sources?.[0];i&&this.dispatchEvent(new CustomEvent("open-source",{detail:i.id}))},this.t("opened"))}render(){const t=this.t;return W`<div class="card">
        <h2>${t("capture_title")}</h2>
        <div class="muted">${t("capture_hint")}</div>
        <div class="ifaces" style="margin-top:12px">
          ${this.interfaces.map(e=>W`<div class="row">
            <b>${e.name}</b><span class="muted">${e.port}</span>
            <span class="grow"></span>
            ${e.recording?W`<span class="chip bad">● ${t("recording",{n:e.recording.frames.toLocaleString(),size:Tt(e.recording.bytes)})}</span>
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
                  <td class="num">${Tt(e.size)}</td>
                  <td class="muted">${It(e.modified,t)}</td>
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
      </div>`}}zt.styles=[Ot,a`
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
    `],t([ut({attribute:!1})],zt.prototype,"interfaces",void 0),t([ut({attribute:!1})],zt.prototype,"offline",void 0),t([ut({attribute:!1})],zt.prototype,"files",void 0),t([ut({attribute:!1})],zt.prototype,"t",void 0),t([ut({attribute:!1})],zt.prototype,"api",void 0),t([mt()],zt.prototype,"message",void 0),t([mt()],zt.prototype,"deleting",void 0),t([mt()],zt.prototype,"busy",void 0),xt("woow-can-capture",zt);const Ft=t=>t.target.value,Ht=t=>t.target.checked;function Bt(t,e=""){if(null==t)return"–";if("boolean"==typeof t)return t?"on":"off";if("number"==typeof t){const i=Number.isInteger(t)?String(t):String(parseFloat(t.toFixed(3)));return e?`${i} ${e.replace("degC","°C").replace("degF","°F")}`:i}return String(t)}class jt extends dt{constructor(){super(...arguments),this.interfaces=[],this.devices=[],this.values={},this.history={},this.charts=[],this.templates=[],this.databases=[],this.preferredInterface="",this.open="",this.draft=null,this.busy=!1,this.message=null,this.deleting="",this.settingsFor="",this.settings={min_interval:"",tolerance:"",timeout:""},this.dbcDevice=null,this.iname=t=>this.interfaces.find(e=>e.id===t)?.name??"?"}async run(t,e){this.busy=!0;try{return await t(),this.message=e?{ok:!0,text:e}:null,!0}catch(t){return this.message={ok:!1,text:this.t("error",{msg:wt(t)})},!1}finally{this.busy=!1}}moreInfo(t){this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:t},bubbles:!0,composed:!0}))}toggleChart(t){this.dispatchEvent(new CustomEvent("toggle-chart",{detail:t}))}startTemplate(){const t=this.templates[0],e=this.interfaces.find(t=>t.id===this.preferredInterface)??this.interfaces[0];this.draft=t?this.draftFor(t,e?.id??""):null,this.message=null}draftFor(t,e){return{template:t.id,entryId:e,name:"",params:Object.fromEntries(t.params.map(t=>[t.key,null===t.default||void 0===t.default?"":String(t.default)])),auto:!0,groups:[]}}async createFromTemplate(){const t=this.draft;if(!t)return;const e=this.templates.find(e=>e.id===t.template),i={};for(const s of e?.params??[]){const e=t.params[s.key]??"";i[s.key]="number"!=typeof s.default||""===e||isNaN(Number(e))?e:Number(e)}let s=null;await this.run(async()=>{s=await this.api.createFromTemplate(t.template,t.entryId,t.name,i,t.auto?null:t.groups)})&&s&&(this.draft=null,this.open=s.id,this.message={ok:!0,text:this.t("created_device",{name:s.name})})}renderTemplateDialog(){const t=this.draft;if(!t)return K;const e=this.t,i=this.templates.find(e=>e.id===t.template),s=e=>this.draft={...t,...e},r=(t,i)=>Dt(`${t}_${i}`)?e(`${t}_${i}`):i;return W`<div class="scrim" @click=${t=>t.target===t.currentTarget&&(this.draft=null)}>
      <div class="dialog">
        <div>
          ${this.templates.map(e=>W`<button class="tpl ${e.id===t.template?"on":""}"
            @click=${()=>this.draft=this.draftFor(e,t.entryId)}>
            <div><b>${e.name}</b></div>
            <div class="muted">${r("category",e.category)} · ${r("confidence",e.confidence)}</div>
          </button>`)}
        </div>
        ${i?W`<div class="form">
              <h2 style="margin:0;font-size:1.15em;font-weight:500">${i.name}</h2>
              <div>${i.description}</div>
              ${i.notes?W`<div class="muted">${i.notes}</div>`:K}
              <div class="row">
                <span class="chip ok">${e("only_listens")}</span>
                <span class="chip">${e("confidence",{x:r("confidence",i.confidence)})}</span>
                ${i.bitrate?W`<span class="chip">${e("kbps",{n:i.bitrate/1e3})}</span>`:K}
              </div>
              <div class="muted">${e("verified_with",{x:i.verified.join("；")})}</div>
              <details>
                <summary>${e("sources")}</summary>
                <ul>${i.source.map(t=>W`<li>${t}</li>`)}</ul>
                <div class="muted">${e("license_x",{x:i.license})}</div>
              </details>
              <label class="field">${e("interface")}
                <select @change=${t=>s({entryId:Ft(t)})}>
                  ${this.interfaces.map(e=>W`<option value=${e.id} ?selected=${e.id===t.entryId}>${e.name} · ${e.port}</option>`)}
                </select>
              </label>
              <label class="field">${e("device_name")}
                <input .value=${t.name} placeholder=${i.default_name} @input=${t=>s({name:Ft(t)})} />
              </label>
              ${i.params.map(e=>W`<label class="field">${e.key} — ${e.description}
                <input .value=${t.params[e.key]??""} @input=${i=>s({params:{...t.params,[e.key]:Ft(i)}})} />
              </label>`)}
              ${i.groups.length?W`<div>
                    <div class="muted">${e("groups_title")}</div>
                    <label class="row"><input type="checkbox" .checked=${t.auto}
                      @change=${t=>s({auto:Ht(t)})} />${e("groups_auto")}</label>
                    ${t.auto?W`<div class="muted">${e("groups_detect_hint")}</div>`:i.groups.map(e=>W`<label class="row"><input type="checkbox" .checked=${t.groups.includes(e.id)}
                          @change=${i=>s({groups:Ht(i)?[...t.groups,e.id]:t.groups.filter(t=>t!==e.id)})} />
                          ${e.name}</label>`)}
                  </div>`:K}
              ${this.message&&!this.message.ok?W`<div class="chip bad" style="white-space:normal">${this.message.text}</div>`:K}
              <div class="row">
                <span class="grow"></span>
                <button @click=${()=>this.draft=null}>${e("cancel")}</button>
                <button class="primary" ?disabled=${this.busy||!t.entryId} @click=${()=>this.createFromTemplate()}>${e("create")}</button>
              </div>
            </div>`:K}
      </div>
    </div>`}async adopt(t,e,i,s){await this.run(()=>this.api.setSignal(t.id,e,i.name,{adopted:s}))}openSettings(t,e,i){const s=`${t.id}|${e}.${i}`;if(this.settingsFor===s)return void(this.settingsFor="");const r=t.definition?.messages.find(t=>t.name===e)?.signals.find(t=>t.name===i),o=r?.entity??{};this.settings={min_interval:void 0!==o.min_interval?String(o.min_interval):"",tolerance:void 0!==o.tolerance?String(o.tolerance):"",timeout:void 0!==o.timeout?String(o.timeout):""},this.settingsFor=s}async applySettings(t,e,i){const s={};for(const t of["min_interval","tolerance","timeout"]){const e=this.settings[t].trim();s[t]=""===e?null:Number(e)}await this.run(()=>this.api.setSignal(t.id,e,i,{entity:s}))&&(this.settingsFor="")}renderDevice(t){const e=this.t,i=this.values[t.id]??{},s=t.status,r=s.reduce((t,e)=>t+e.signals.filter(t=>t.adopted).length,0),o=s.filter(t=>!0===t.fresh).length,a=s.filter(t=>!1===t.fresh&&null!==t.seen_s_ago).length,n=s.filter(t=>null===t.seen_s_ago).length,c=this.open===t.id;return W`<div class="device">
      <div class="row">
        <h3>${t.name}</h3>
        <span class="chip">${this.iname(t.interface)}</span>
        ${t.template?W`<span class="chip info">${this.templates.find(e=>e.id===t.template)?.name??t.template}</span>`:K}
        ${t.source.startsWith("dbc:")?W`<span class="chip info">${t.source.slice(4)}</span>`:K}
        <span class="grow"></span>
        <button class="link" @click=${()=>this.open=c?"":t.id}>${c?"▲":"▼"}</button>
      </div>
      <div class="muted">
        ${e("messages_n",{n:s.length})} · ${e("entities_n",{n:r})}
        ${o?W` · <span class="rx">${o} ${e("fresh")}</span>`:K}
        ${a?W` · <span style="color:var(--warning-color)">${a} ${e("stale")}</span>`:K}
        ${n?W` · ${n} ${e("never_seen")}`:K}
      </div>
      ${c?W`${s.map(s=>W`<div class="msg">
              <div class="row">
                <b>${s.name}</b><span class="muted mono">${s.id}</span>
                <span class="chip ${!0===s.fresh?"ok":!1===s.fresh&&null!==s.seen_s_ago?"warn":""}">
                  ${null===s.seen_s_ago?e("never_seen"):!1===s.fresh?e("stale"):e("fresh")}</span>
              </div>
              <div class="wrap"><table>
                <colgroup><col class="c-adopt" /><col class="c-name" /><col class="c-value" /><col /><col class="c-actions" /></colgroup>
                <tbody>
                  ${s.signals.map(r=>{const o=`${s.name}.${r.name}`,a=o in i?i[o]:r.value,n=`${t.id}|${o}`,c="number"==typeof a&&"binary_sensor"!==r.platform;return W`<tr>
                        <td><input type="checkbox" title=${e("adopt_hint")} .checked=${r.adopted}
                          @change=${e=>this.adopt(t,s.name,r,Ht(e))} /></td>
                        <td>${r.name}</td>
                        <td class="val">${"binary_sensor"!==r.platform||0!==a&&1!==a&&"boolean"!=typeof a?Bt(a,r.unit):e(1===a||!0===a?"state_on":"state_off")}</td>
                        <td title=${r.entity_id??""}>${r.entity_id?r.disabled?W`<span class="off-entity">${r.entity_id} · ${e("entity_disabled")}</span>`:W`<a class="entity" @click=${()=>this.moreInfo(r.entity_id)}>${r.entity_id}</a>`:K}</td>
                        <td class="row">
                          ${c||this.charts.includes(n)?W`<button class="link" @click=${()=>this.toggleChart(n)}>
                                ${this.charts.includes(n)?"✓ ":""}${e("chart")}</button>`:K}
                          ${r.adopted?W`<button class="link" @click=${()=>this.openSettings(t,s.name,r.name)}>${e("settings")}</button>`:K}
                        </td>
                      </tr>
                      ${this.settingsFor===n?W`<tr><td colspan="5"><div class="inline">
                            ${["min_interval","tolerance","timeout"].map(t=>W`<label class="field">
                              ${e("timeout"===t?"timeout_s":t)}
                              <input type="number" step="any" .value=${this.settings[t]}
                                @input=${e=>this.settings={...this.settings,[t]:Ft(e)}} /></label>`)}
                            <button class="primary" @click=${()=>this.applySettings(t,s.name,r.name)}>${e("apply")}</button>
                          </div></td></tr>`:K}`})}
                </tbody>
              </table></div>
            </div>`)}
            <div class="row">
              <button class="link" @click=${()=>this.run(()=>this.api.download(`/api/woow_can/devices/${t.id}/dbc`))}>
                ${e("download_dbc")}</button>
              <span class="grow"></span>
              ${this.deleting===t.id?W`<span>${e("delete_device_confirm",{name:t.name})}</span>
                    <button class="danger" @click=${()=>this.run(async()=>{this.deleting="",await this.api.deleteDevice(t.id)})}>${e("delete")}</button>
                    <button @click=${()=>this.deleting=""}>${e("cancel")}</button>`:W`<button class="link danger" @click=${()=>this.deleting=t.id}>${e("delete")}</button>`}
            </div>`:K}
    </div>`}renderCharts(){const t=this.t;return this.charts.length?W`<div class="card">
      <div class="row"><h2 class="grow">${t("charts_title")}</h2></div>
      <div class="charts">
        ${this.charts.map(t=>{const[e,i]=t.split("|"),s=this.devices.find(t=>t.id===e),r=this.history[t]??[];let o="";for(const t of s?.status??[])for(const e of t.signals)`${t.name}.${e.name}`===i&&(o=e.unit);const a=this.values[e]?.[i],n=r.map(t=>t[1]),c=n.length?Math.min(...n):0,d=n.length?Math.max(...n):1,l=d-c||1,h=r.length?r[0][0]:0,p=(r.length?r[r.length-1][0]:1)-h||1,u=r.map(([t,e])=>`${((t-h)/p*300).toFixed(1)},${(56-(e-c)/l*52).toFixed(1)}`);return W`<div class="chart">
            <div class="row"><span class="muted grow">${s?.name??"?"} · ${i}</span>
              <button class="link" @click=${()=>this.toggleChart(t)}>✕</button></div>
            <b>${Bt(a,o)}</b>
            <svg class="line" viewBox="0 0 300 60" preserveAspectRatio="none">
              ${q`<line x1="0" y1="58" x2="300" y2="58"></line>`}
              ${u.length>1?q`<polyline points=${u.join(" ")}></polyline>`:K}
            </svg>
            <div class="muted">${n.length?`${Bt(c)} – ${Bt(d)}`:""}</div>
          </div>`})}
      </div>
    </div>`:K}async upload(t){const e=t.target,i=e.files?.[0];if(e.value="",!i)return;const s=this.preferredInterface&&this.interfaces.some(t=>t.id===this.preferredInterface)?[this.preferredInterface]:[];await this.run(async()=>{const t=await this.api.uploadDbc(i,s);this.message={ok:!0,text:this.t("imported_dbc",{name:t.name,m:t.messages,s:t.signals})}})}async setAttach(t,e,i){const s=i?[...t.attached.filter(t=>t!==e),e]:t.attached.filter(t=>t!==e);await this.run(()=>this.api.dbc("attach",t.name,{interfaces:s}))}async createFromDbc(){const t=this.dbcDevice;if(!t)return;await this.run(()=>this.api.dbc("create_device",t.name,{entry_id:t.entryId,device_name:t.deviceName,messages:t.messages.length?t.messages:void 0}))&&(this.dbcDevice=null)}renderDatabases(){const t=this.t;return W`<div class="card">
      <div class="row">
        <h2 class="grow">${t("dbc_title")}</h2>
        <button @click=${()=>this.renderRoot.querySelector("#dbc")?.click()}>${t("import_dbc")}</button>
        <input id="dbc" type="file" accept=".dbc" @change=${this.upload} />
      </div>
      <div class="muted">${t("dbc_hint")}</div>
      ${0===this.databases.length?W`<div class="empty">${t("dbc_empty")}</div>`:this.databases.map(e=>W`<div class="device" style="margin-top:10px">
            <div class="row">
              <b class="mono">${e.name}</b>
              <span class="muted">${t("messages_n",{n:e.messages})} · ${e.signals}</span>
              ${e.warning_count?W`<details><summary>${t("dbc_warnings",{n:e.warning_count})}</summary>
                <ul>${e.warnings.map(t=>W`<li class="mono">${t}</li>`)}</ul></details>`:K}
              <span class="grow"></span>
              <button class="link" @click=${()=>this.api.download(`/api/woow_can/dbc/${encodeURIComponent(e.name)}`)}>${t("download")}</button>
              <button class="link" @click=${()=>this.dbcDevice={name:e.name,entryId:this.preferredInterface||this.interfaces[0]?.id||"",deviceName:"",messages:[]}}>${t("make_device")}</button>
              <button class="link danger" @click=${()=>this.run(()=>this.api.dbc("delete",e.name))}>${t("delete")}</button>
            </div>
            <div class="row">
              <span class="muted">${t("dbc_attached_to")}:</span>
              <label class="row"><input type="checkbox" .checked=${e.attached.includes("*")}
                @change=${t=>this.setAttach(e,"*",Ht(t))} />${t("all_interfaces")}</label>
              ${this.interfaces.map(t=>W`<label class="row"><input type="checkbox" .checked=${e.attached.includes(t.id)}
                @change=${i=>this.setAttach(e,t.id,Ht(i))} />${t.name}</label>`)}
            </div>
            ${this.dbcDevice?.name===e.name?W`<div class="inline">
                  <label class="field">${t("interface")}
                    <select @change=${t=>this.dbcDevice={...this.dbcDevice,entryId:Ft(t)}}>
                      ${this.interfaces.map(t=>W`<option value=${t.id} ?selected=${t.id===this.dbcDevice.entryId}>${t.name}</option>`)}
                    </select></label>
                  <label class="field">${t("device_name")}<input .value=${this.dbcDevice.deviceName} placeholder=${e.name.replace(/\.dbc$/i,"")}
                    @input=${t=>this.dbcDevice={...this.dbcDevice,deviceName:Ft(t)}} /></label>
                  <div>
                    <div class="muted">${t("choose_messages")}</div>
                    ${e.message_names.map(t=>W`<label class="row"><input type="checkbox" .checked=${this.dbcDevice.messages.includes(t)}
                      @change=${e=>this.dbcDevice={...this.dbcDevice,messages:Ht(e)?[...this.dbcDevice.messages,t]:this.dbcDevice.messages.filter(e=>e!==t)}} />
                      <span class="mono">${t}</span></label>`)}
                  </div>
                  <button class="primary" ?disabled=${this.busy} @click=${()=>this.createFromDbc()}>${t("create")}</button>
                  <button @click=${()=>this.dbcDevice=null}>${t("cancel")}</button>
                </div>`:K}
          </div>`)}
    </div>`}render(){const t=this.t;return W`<div class="card">
        <div class="row">
          <h2 class="grow">${t("tab_devices")}</h2>
          <button class="primary" ?disabled=${!this.templates.length||!this.interfaces.length} @click=${()=>this.startTemplate()}>
            ${t("add_from_template")}</button>
        </div>
        <div class="muted">${t("devices_hint")}</div>
        ${this.message&&!this.draft?W`<div class="chip ${this.message.ok?"ok":"bad"}" style="margin-top:8px;white-space:normal">${this.message.text}</div>`:K}
        ${0===this.devices.length?W`<div class="empty">${t("devices_empty")}</div>`:W`<div class="devices" style="margin-top:12px">${this.devices.map(t=>this.renderDevice(t))}</div>`}
      </div>
      ${this.renderCharts()} ${this.renderDatabases()} ${this.renderTemplateDialog()}`}}jt.styles=[Ot,a`
      .devices {
        display: grid;
        gap: 12px;
      }
      .device {
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 10px;
        padding: 10px 12px;
        display: grid;
        gap: 6px;
      }
      .device h3 {
        margin: 0;
        font-size: 1.05em;
        font-weight: 500;
      }
      .msg {
        border-top: 1px solid var(--divider-color, #eee);
        padding-top: 6px;
        margin-top: 4px;
      }
      .wrap {
        overflow-x: auto;
      }
      table {
        border-collapse: collapse;
        width: 100%;
        font-size: 0.92em;
        table-layout: fixed;
        min-width: 640px;
      }
      col.c-adopt {
        width: 32px;
      }
      col.c-name {
        width: 26%;
      }
      col.c-value {
        width: 16%;
      }
      col.c-actions {
        width: 110px;
      }
      td {
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .off-entity {
        color: var(--secondary-text-color);
      }
      td,
      th {
        padding: 4px 8px;
        text-align: left;
        border-bottom: 1px solid var(--divider-color, #f0f0f0);
        white-space: nowrap;
        vertical-align: middle;
      }
      th {
        color: var(--secondary-text-color);
        font-weight: 500;
      }
      td.val {
        font-variant-numeric: tabular-nums;
        font-weight: 500;
      }
      .charts {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(min(100%, 260px), 1fr));
        gap: 12px;
      }
      .chart {
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 10px;
        padding: 8px 10px;
        display: grid;
        gap: 2px;
      }
      .chart b {
        font-size: 1.3em;
        font-variant-numeric: tabular-nums;
      }
      svg.line {
        width: 100%;
        height: 60px;
        display: block;
      }
      svg.line polyline {
        fill: none;
        stroke: var(--primary-color);
        stroke-width: 1.5;
      }
      svg.line line {
        stroke: var(--divider-color, #ddd);
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
        width: min(860px, 100%);
        max-height: 90vh;
        overflow: auto;
        background: var(--card-background-color, #fff);
        border-radius: 12px;
        padding: 20px;
        display: grid;
        grid-template-columns: minmax(180px, 1fr) 2fr;
        gap: 16px;
      }
      @media (max-width: 640px) {
        .dialog {
          grid-template-columns: 1fr;
        }
      }
      .tpl {
        display: block;
        width: 100%;
        text-align: left;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 6px;
        background: none;
      }
      .tpl.on {
        border-color: var(--primary-color);
        background: rgba(3, 169, 244, 0.06);
      }
      label.field {
        display: grid;
        gap: 4px;
        font-size: 0.85em;
        color: var(--secondary-text-color);
      }
      label.field input,
      label.field select {
        font-size: 1.05em;
        color: var(--primary-text-color);
      }
      .form {
        display: grid;
        gap: 10px;
        align-content: start;
      }
      details summary {
        cursor: pointer;
        color: var(--secondary-text-color);
      }
      .inline {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: end;
        padding: 8px;
        border-radius: 8px;
        background: var(--secondary-background-color, #f5f5f5);
      }
      .inline input {
        width: 7em;
      }
      input[type="file"] {
        display: none;
      }
      a.entity {
        color: var(--primary-color);
        cursor: pointer;
        text-decoration: none;
      }
    `],t([ut({attribute:!1})],jt.prototype,"interfaces",void 0),t([ut({attribute:!1})],jt.prototype,"devices",void 0),t([ut({attribute:!1})],jt.prototype,"values",void 0),t([ut({attribute:!1})],jt.prototype,"history",void 0),t([ut({attribute:!1})],jt.prototype,"charts",void 0),t([ut({attribute:!1})],jt.prototype,"templates",void 0),t([ut({attribute:!1})],jt.prototype,"databases",void 0),t([ut({attribute:!1})],jt.prototype,"preferredInterface",void 0),t([ut({attribute:!1})],jt.prototype,"t",void 0),t([ut({attribute:!1})],jt.prototype,"api",void 0),t([mt()],jt.prototype,"open",void 0),t([mt()],jt.prototype,"draft",void 0),t([mt()],jt.prototype,"busy",void 0),t([mt()],jt.prototype,"message",void 0),t([mt()],jt.prototype,"deleting",void 0),t([mt()],jt.prototype,"settingsFor",void 0),t([mt()],jt.prototype,"settings",void 0),t([mt()],jt.prototype,"dbcDevice",void 0),xt("woow-can-devices",jt);const Lt=2;let Wt=class{constructor(t){}get _$AU(){return this._$AM._$AU}_$AT(t,e,i){this._$Ct=t,this._$AM=e,this._$Ci=i}_$AS(t,e){return this.update(t,e)}update(t,e){return this.render(...e)}};const{I:qt}=at,Vt=t=>t,Kt=()=>document.createComment(""),Jt=(t,e,i)=>{const s=t._$AA.parentNode,r=void 0===e?t._$AB:e._$AA;if(void 0===i){const e=s.insertBefore(Kt(),r),o=s.insertBefore(Kt(),r);i=new qt(e,o,t,t.options)}else{const e=i._$AB.nextSibling,o=i._$AM,a=o!==t;if(a){let e;i._$AQ?.(t),i._$AM=t,void 0!==i._$AP&&(e=t._$AU)!==o._$AU&&i._$AP(e)}if(e!==r||a){let t=i._$AA;for(;t!==e;){const e=Vt(t).nextSibling;Vt(s).insertBefore(t,r),t=e}}}return i},Zt=(t,e,i=t)=>(t._$AI(e,i),t),Xt={},Gt=(t,e=Xt)=>t._$AH=e,Qt=t=>{t._$AR(),t._$AA.remove()},Yt=(t,e,i)=>{const s=new Map;for(let r=e;r<=i;r++)s.set(t[r],r);return s},te=(t=>(...e)=>({_$litDirective$:t,values:e}))(class extends Wt{constructor(t){if(super(t),t.type!==Lt)throw Error("repeat() can only be used in text expressions")}dt(t,e,i){let s;void 0===i?i=e:void 0!==e&&(s=e);const r=[],o=[];let a=0;for(const e of t)r[a]=s?s(e,a):a,o[a]=i(e,a),a++;return{values:o,keys:r}}render(t,e,i){return this.dt(t,e,i).values}update(t,[e,i,s]){const r=(t=>t._$AH)(t),{values:o,keys:a}=this.dt(e,i,s);if(!Array.isArray(r))return this.ut=a,o;const n=this.ut??=[],c=[];let d,l,h=0,p=r.length-1,u=0,m=o.length-1;for(;h<=p&&u<=m;)if(null===r[h])h++;else if(null===r[p])p--;else if(n[h]===a[u])c[u]=Zt(r[h],o[u]),h++,u++;else if(n[p]===a[m])c[m]=Zt(r[p],o[m]),p--,m--;else if(n[h]===a[m])c[m]=Zt(r[h],o[m]),Jt(t,c[m+1],r[h]),h++,m--;else if(n[p]===a[u])c[u]=Zt(r[p],o[u]),Jt(t,r[h],r[p]),p--,u++;else if(void 0===d&&(d=Yt(a,u,m),l=Yt(n,h,p)),d.has(n[h]))if(d.has(n[p])){const e=l.get(a[u]),i=void 0!==e?r[e]:null;if(null===i){const e=Jt(t,r[h]);Zt(e,o[u]),c[u]=e}else c[u]=Zt(i,o[u]),Jt(t,r[h],i),r[e]=null;u++}else Qt(r[p]),p--;else Qt(r[h]),h++;for(;u<=m;){const e=Jt(t,c[m+1]);Zt(e,o[u]),c[u++]=e}for(;h<=p;){const t=r[h++];null!==t&&Qt(t)}return this.ut=a,Gt(t,c),V}}),ee=2e3,ie={rise:"#00bbff",fall:"#ff3b30",churn:"#6656a9"},se=()=>({t:-1e9,dir:0,same:0,kind:"",bitT:new Array(8).fill(-1e9),notch:0});function re(t){const e=[];for(let i=0;i+1<t.length;i+=2)e.push(parseInt(t.slice(i,i+2),16));return e}const oe=t=>t.target.value;class ae extends dt{constructor(){super(...arguments),this.interfaces=[],this.offline=[],this.source="",this.paused=!1,this.bin=!1,this.filterText="",this.changingOnly=!1,this.hideInactive=!1,this.expanded=-1,this.message="",this.trace=[],this.traceNext=null,this.traceBusy=!1,this.traceDir="",this.frames=0,this.overflow=0,this.tick=0,this.narrow=!1,this.decoded=null,this.rows=new Map,this.names=new Map,this.decodedAt=0,this.decodedKey=-1,this.order=[],this.orderDirty=!0,this.pins=new Set,this.token="",this.subscribed="",this.serverOffset=0,this.traceEnd=null,this.resize=new ResizeObserver(t=>{const e=t[0]?.contentRect.width??1e3;e<640!==this.narrow&&(this.narrow=e<640)}),this.onVisibility=()=>{document.hidden?this.stop():this.paused||this.start()}}connectedCallback(){super.connectedCallback(),document.addEventListener("visibilitychange",this.onVisibility),this.resize.observe(this),this.timer=window.setInterval(()=>{this.paused||document.hidden||(this.tick++,this.expanded>=0&&performance.now()-this.decodedAt>1e3&&this.refreshDecode())},200),this.loadPins(),this.source&&!this.paused&&this.start()}disconnectedCallback(){super.disconnectedCallback(),document.removeEventListener("visibilitychange",this.onVisibility),this.resize.disconnect(),window.clearInterval(this.timer),window.clearTimeout(this.retry),this.stop()}updated(t){t.has("source")&&this.source!==this.subscribed&&(this.paused=!1,this.trace=[],this.loadPins(),this.start())}get live(){return this.interfaces.some(t=>t.id===this.source)}get iface(){return this.interfaces.find(t=>t.id===this.source)}loadPins(){this.pins=new Set(kt(`woow_can.pins.${this.source}`,[])),this.orderDirty=!0}savePins(){At(`woow_can.pins.${this.source}`,[...this.pins])}async start(){if(await this.stop(),!this.source||document.hidden)return;const t=this.source;this.rows.clear(),this.orderDirty=!0,this.token=Math.random().toString(36).slice(2,12)+Date.now().toString(36);const e=this.token;this.subscribed=t;try{const i=await this.api.subscribeMonitor(t,e,t=>this.onBatch(t,e));if(this.token!==e)return void i();this.unsub=i}catch(t){this.message=wt(t)}}async stop(){const t=this.unsub;if(this.unsub=void 0,this.token="",t)try{await t()}catch{}}onBatch(t,e){if(e!==this.token)return;if(t.gone)return this.message=t.error??this.t("gone"),window.clearTimeout(this.retry),void(this.retry=window.setTimeout(()=>!this.paused&&void this.start(),1500));const i=performance.now();this.serverOffset=t.t-Date.now()/1e3,(t.full||t.clear)&&(this.rows.clear(),this.orderDirty=!0),t.full&&this.names.clear();for(const[e,i]of Object.entries(t.names??{}))this.names.set(Number(e)%ft,i);for(const e of t.rows??[])this.applyRow(e,i,!!t.full);void 0!==t.frames&&(this.frames=t.frames),void 0!==t.overflow&&(this.overflow=t.overflow),void 0!==t.trace_end&&(this.traceEnd=t.trace_end),this.message===this.t("gone")&&(this.message=""),t.seq>0&&this.api.ack(e,t.seq).catch(()=>{})}applyRow(t,e,i){const[s,r,o,a,n,c,d,l,h,p,u,m]=t,f=re(a);let v=this.rows.get(s);if(v){if(h){const t=c?c/1e6:1;for(let i=0;i<f.length;i++){const s=parseInt(h.slice(2*i,2*i+2)||"0",16);if(!s)continue;const r=v.b[i]??=se();for(let t=0;t<8;t++)s>>t&1&&(r.bitT[t]=e);if(!(s&~r.notch&255))continue;const o=v.bytes[i]??0,a=f[i]>o?1:f[i]<o?-1:0,n=e-r.t>10*t*1e3;r.same=0!==a&&a===r.dir?r.same+1:1,r.dir=a,r.kind=0===a?"churn":n||r.same>8?a>0?"rise":"fall":"churn",r.t=e}v.b.length!==f.length&&(v.b=f.map((t,e)=>v.b[e]??se()))}}else v={key:s,raw:r,flags:o,hex:a,bytes:f,count:n,period:0,pmin:0,pmax:0,last:p,changed:u,changedPrev:m,born:i?0:e,b:f.map(()=>se())},this.rows.set(s,v),this.orderDirty=!0;Object.assign(v,{raw:r,flags:o,hex:a,bytes:f,count:n,last:p,changed:u,changedPrev:m,period:c/1e6,pmin:d/1e6,pmax:l/1e6})}serverNow(){return Date.now()/1e3+this.serverOffset}notch(){const t=performance.now();let e=0;for(const i of this.rows.values())for(const s of i.b)s.bitT.forEach((i,r)=>{t-i<2e3&&!(s.notch>>r&1)&&(s.notch|=1<<r,e++)});this.message=e?this.t("notch_added",{n:e}):this.t("notch_none")}clearNotch(){for(const t of this.rows.values())for(const e of t.b)e.notch=0;this.message=""}async clear(){try{await this.api.clearMonitor(this.source)}catch(t){this.message=wt(t)}}async pause(t){void 0!==t&&(this.filterText=t),this.paused=!0,await this.stop(),this.trace=[],this.traceNext=this.traceEnd,await this.loadTrace(!0)}resume(){this.paused=!1,this.trace=[],this.start()}async loadTrace(t=!1){if(!this.traceBusy){this.traceBusy=!0;try{const e=new bt(this.filterText),i=await this.api.trace(this.source,{before:t?this.traceEnd:this.traceNext,limit:200,ids:e.error||e.all?"":this.filterText,direction:this.traceDir||null});this.trace=t?i.frames:[...this.trace,...i.frames],this.traceNext=i.next}catch(t){this.message=wt(t)}finally{this.traceBusy=!1}}}async refreshDecode(){const t=this.rows.get(this.expanded);if(this.decodedAt=performance.now(),!t||16&t.flags)this.decoded=null;else{this.decodedKey!==t.key&&(this.decoded=null),this.decodedKey=t.key;try{const e=await this.api.decode(this.source,t.raw,t.hex);this.expanded===t.key&&(this.decoded=e.decoded)}catch{this.decoded=null}}}toggleRow(t){this.expanded=this.expanded===t?-1:t,this.decoded=null,this.decodedAt=0,this.expanded>=0&&this.refreshDecode()}togglePin(t){this.pins.has(t)?this.pins.delete(t):this.pins.add(t),this.pins=new Set(this.pins),this.savePins(),this.orderDirty=!0,this.requestUpdate()}sendAgain(t){this.dispatchEvent(new CustomEvent("send-frame",{detail:{frame:gt(t.raw,t.flags,t.hex),entryId:this.live?this.source:""}}))}async fireEvents(t){const e=this.iface;if(!e)return;const i=_t(t.raw),s=e.settings.event_filter.trim();try{await this.api.setEvents(e.id,s?`${s}, ${i}`:i),this.message=this.t("events_added",{id:i})}catch(t){this.message=wt(t)}}notchRow(t){for(const e of t.b)e.notch=255;this.requestUpdate()}sorted(){return this.orderDirty&&(this.order=[...this.rows.values()].sort((t,e)=>{const i=this.pins.has(t.key)?0:1,s=this.pins.has(e.key)?0:1;if(i!==s)return i-s;const r=vt(t.raw)?1:0,o=vt(e.raw)?1:0;if(r!==o)return r-o;const a=t.raw%536870912,n=e.raw%536870912;return a!==n?a-n:t.key-e.key}).map(t=>t.key),this.orderDirty=!1),this.order.map(t=>this.rows.get(t)).filter(t=>!!t)}byteCells(t,e){return t.bytes.map((i,s)=>{const r=t.b[s];let o="";if(r?.kind){const t=Math.max(0,1-(e-r.t)/ee)*("churn"===r.kind?.4:.65);t>.01&&(o=`background: color-mix(in srgb, ${ie[r.kind]} ${Math.round(100*t)}%, transparent)`)}const a=this.bin?i.toString(2).padStart(8,"0"):i.toString(16).toUpperCase().padStart(2,"0");return W`<span class="byte ${this.bin?"bin":""} ${r?.notch?"notched":""}" style=${o}>${a}</span>`})}detailRow(t,e){return W`<tr class="detail"><td colspan="9">${this.detail(t,e)}</td></tr>`}detail(t,e){const i=this.t,s=this.pins.has(t.key),r=this.iface,o=r?new bt(r.settings.event_filter):null,a=!!(r&&r.settings.event_filter.trim()&&o&&!o.error&&o.matches(t.raw)),n=this.decodedKey===t.key?this.decoded:null;return W`
        <div class="mono">${gt(t.raw,t.flags,t.hex)}</div>
        ${null===n?K:0===n.length?W`<div class="muted">${i("no_definition")}</div>`:n.map(t=>W`<div class="decoded">
                <span class="muted">${t.source} · ${t.message}</span>
                ${t.signals.map(t=>W`<span class="sig">${t.name} <b>${Bt(t.value,t.unit)}</b></span>`)}
              </div>`)}
        <div class="muted">
          ${t.period?W`${i("detail_period",{avg:(1e3*t.period).toFixed(t.period<.1?2:1),min:(1e3*t.pmin).toFixed(1),max:(1e3*t.pmax).toFixed(1)})} · ${i("detail_rate",{hz:(1/t.period).toFixed(2)})}`:K}
        </div>
        ${t.changedPrev?W`<div class="muted">
              ${i("detail_changed",{ago:It(t.changed,i,e),gap:Mt(t.changed-t.changedPrev)})}
            </div>`:K}
        <div class="actions">
          <button @click=${()=>this.togglePin(t.key)}>${i(s?"row_unpin":"row_pin")}</button>
          <button @click=${()=>this.sendAgain(t)}>${i("row_send")}</button>
          ${r?W`<button ?disabled=${a} @click=${()=>this.fireEvents(t)}>
                ${i(a?"row_events_on":"row_events")}
              </button>`:K}
          <button @click=${()=>this.pause(_t(t.raw))}>${i("row_trace")}</button>
          <button @click=${()=>this.notchRow(t)}>${i("row_notch")}</button>
        </div>`}renderLive(){const t=this.t,e=performance.now(),i=this.serverNow(),s=new bt(this.filterText),r=this.sorted().filter(t=>!(!s.error&&!s.matches(t.raw))&&((!this.changingOnly||t.changedPrev>0&&i-t.changed<5)&&!(this.hideInactive&&i-t.last>5)));return this.rows.size?this.narrow?this.renderCards(r,e,i):W`<div class="wrap">
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
          ${te(r,t=>t.key,s=>{const r=i-s.last,o=r>(s.period?5*s.period+.5:1.75),a=s.key>=ft,n=!a&&!!(8&s.flags)&&!this.iface?.virtual;return W`<tr class="${o?"inactive":""} ${s.born&&e-s.born<ee?"new":""}">
                  <td><button class="pin ${this.pins.has(s.key)?"on":""}" title=${t("row_pin")}
                    @click=${()=>this.togglePin(s.key)}>${this.pins.has(s.key)?"★":"☆"}</button></td>
                  <td class="id ${r>4?"stale":""}" @click=${()=>this.toggleRow(s.key)}>
                    ${_t(s.raw)}${a?W`<span class="tag">${t("dir_tx")}</span>`:K}${n?W`<span class="tag muted-tag">${t("dir_local")}</span>`:K}${this.names.has(s.key%ft)?W`<div class="name">${this.names.get(s.key%ft)}</div>`:K}
                  </td>
                  <td class="num">${s.bytes.length}</td>
                  <td><div class="bytes">${this.byteCells(s,e)}</div></td>
                  <td class="num">${s.count.toLocaleString()}</td>
                  <td class="num">${s.period?(1/s.period).toFixed(1):"–"}</td>
                  <td class="num">${s.period?Mt(s.period):"–"}</td>
                  <td class="num">${s.changedPrev?Mt(s.changed-s.changedPrev):"–"}</td>
                  <td class="num">${Mt(Math.max(0,r))}</td>
                </tr>
                ${this.expanded===s.key?this.detailRow(s,i):K}`})}
        </tbody>
      </table>
    </div>`:W`<div class="empty">${t("monitor_empty")}</div>`}renderCards(t,e,i){const s=this.t;return W`<div class="cards">
      ${te(t,t=>t.key,t=>{const r=i-t.last,o=r>(t.period?5*t.period+.5:1.75),a=t.key>=ft;return W`<div class="mrow ${o?"inactive":""} ${t.born&&e-t.born<ee?"new":""}">
            <div class="mhead" @click=${()=>this.toggleRow(t.key)}>
              <button class="pin ${this.pins.has(t.key)?"on":""}" @click=${e=>{e.stopPropagation(),this.togglePin(t.key)}}>${this.pins.has(t.key)?"★":"☆"}</button>
              <span class="id ${r>4?"stale":""}">${_t(t.raw)}</span>
              ${a?W`<span class="tag">${s("dir_tx")}</span>`:K}
              ${this.names.has(t.key%ft)?W`<span class="muted">${this.names.get(t.key%ft)}</span>`:K}
              <span class="grow"></span>
              <span class="muted">${t.period?`${(1/t.period).toFixed(1)} Hz · `:""}${Mt(Math.max(0,r))}</span>
            </div>
            <div class="bytes wrapbytes">${this.byteCells(t,e)}</div>
            ${this.expanded===t.key?W`<div class="mdetail">${this.detail(t,i)}</div>`:K}
          </div>`})}
    </div>`}renderTrace(){const t=this.t,e=this.trace;return W`<div class="row msg">
        <b class="grow">${t("paused_title")}</b>
        <select @change=${t=>{this.traceDir=oe(t),this.loadTrace(!0)}}>
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
                ${e.map(([i,s,r,o,a],n)=>{const c=e[n+1],d=!!(16&o),l=!!(4&o);return W`<tr title=${`#${i}`}>
                    <td class="num">${Nt(s)}</td>
                    ${this.narrow?K:W`<td class="num">${c?Mt(s-c[1]):""}</td>`}
                    <td>${t(l?"dir_tx":"dir_rx")}</td>
                    <td class="id">${d?W`<span class="tag err">ERR</span>`:_t(r)}</td>
                    ${this.narrow?K:W`<td class="num">${a.length/2}</td>`}
                    <td><div class="bytes">
                      ${d?W`<span class="muted">${t("trace_error",{x:gt(r,o,a)})}</span>`:re(a).map(t=>W`<span class="byte ${this.bin?"bin":""}">${this.bin?t.toString(2).padStart(8,"0"):t.toString(16).toUpperCase().padStart(2,"0")}</span>`)}
                    </div></td>
                  </tr>`})}
              </tbody>
            </table>
          </div>`}
      <div class="row msg">
        ${null!==this.traceNext?W`<button ?disabled=${this.traceBusy} @click=${()=>this.loadTrace()}>${t("trace_older")}</button>`:e.length?W`<span class="muted">${t("trace_start")}</span>`:K}
      </div>`}render(){const t=this.t;this.tick;const e=this.offline.find(t=>t.id===this.source),i=new bt(this.filterText);return W`<div class="card">
      <div class="toolbar">
        <select title=${t("source")} @change=${t=>this.dispatchEvent(new CustomEvent("source-changed",{detail:oe(t)}))}>
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
          @input=${t=>this.filterText=oe(t)}
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
    </div>`}}ae.styles=[Ot,Rt,a`
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
      td.id .name {
        font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
        font-weight: 400;
        font-size: 0.8em;
        color: var(--secondary-text-color);
      }
      .decoded {
        display: flex;
        flex-wrap: wrap;
        gap: 4px 14px;
        margin: 4px 0;
      }
      .decoded .sig {
        font-variant-numeric: tabular-nums;
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
    `],t([ut({attribute:!1})],ae.prototype,"interfaces",void 0),t([ut({attribute:!1})],ae.prototype,"offline",void 0),t([ut({attribute:!1})],ae.prototype,"source",void 0),t([ut({attribute:!1})],ae.prototype,"t",void 0),t([ut({attribute:!1})],ae.prototype,"api",void 0),t([mt()],ae.prototype,"paused",void 0),t([mt()],ae.prototype,"bin",void 0),t([mt()],ae.prototype,"filterText",void 0),t([mt()],ae.prototype,"changingOnly",void 0),t([mt()],ae.prototype,"hideInactive",void 0),t([mt()],ae.prototype,"expanded",void 0),t([mt()],ae.prototype,"message",void 0),t([mt()],ae.prototype,"trace",void 0),t([mt()],ae.prototype,"traceNext",void 0),t([mt()],ae.prototype,"traceBusy",void 0),t([mt()],ae.prototype,"traceDir",void 0),t([mt()],ae.prototype,"frames",void 0),t([mt()],ae.prototype,"overflow",void 0),t([mt()],ae.prototype,"tick",void 0),t([mt()],ae.prototype,"narrow",void 0),t([mt()],ae.prototype,"decoded",void 0),xt("woow-can-monitor",ae);const ne={error_active:"ok",error_warning:"warn",error_passive:"warn",bus_off:"bad",stopped:"",sleeping:"",virtual:"info"};class ce extends dt{constructor(){super(...arguments),this.interfaces=[],this.history={}}stateLabel(t){if(!t.available)return this.t("unavailable");const e=String(t.status.state??"unknown"),i=`state_${e}`;return Dt(i)?this.t(i):e}sparkline(t){if(t.length<2)return K;const e=Math.max(10,...t),i=300,s=36,r=i/(t.length-1),o=t.map((t,i)=>`${(i*r).toFixed(1)},${(34-t/e*32).toFixed(1)}`);return W`<svg class="spark" viewBox="0 0 ${i} ${s}" preserveAspectRatio="none" role="img" aria-label=${this.t("sparkline")}>
      ${q`<line x1="0" y1=${35} x2=${i} y2=${35}></line>
        <polygon points=${`0,35 ${o.join(" ")} 300,35`}></polygon>
        <polyline points=${o.join(" ")}></polyline>`}
    </svg>`}hints(t){const e=this.t,i=t.status,s=[];return t.settings.listen_only&&!t.virtual&&s.push({cls:"info",text:e("hint_listen_only")}),"bus_off"===i.state?s.push({cls:"bad",text:t.settings.restart_ms?e("hint_bus_off_auto",{ms:t.settings.restart_ms}):e("hint_bus_off_manual")}):"error_passive"===i.state&&Number(i.tx_error_counter??0)>=128&&s.push({cls:"warn",text:e("hint_passive")}),Number(i.rx_over_errors??0)>0&&s.push({cls:"warn",text:e("hint_overflow",{n:Number(i.rx_over_errors)})}),Number(i.socket_drops??0)>0&&s.push({cls:"warn",text:e("hint_socket_drops",{n:Number(i.socket_drops)})}),s}card(t){const e=this.t,i=t.status,s=t.load,r=i.berr_reporting?`${i.bus_error??0} · ${e("arbitration_lost")} ${i.arbitration_lost??0}`:i.berr_supported?e("reporting_off"):e("not_supported"),o=t.virtual?[e("virtual_iface")]:[e("kbps",{n:Math.round(t.settings.bitrate/1e3)}),...t.settings.fd?[e("can_fd")]:[],...t.settings.listen_only?[e("listen_only")]:[]],a=t.errors.last,n=String(i.state??"");return W`<div class="card">
      <div class="head">
        <b>${t.name}</b>
        <span class="muted">${t.port} · ${t.driver||"?"} · ${o.join(" · ")}</span>
        <span class="grow"></span>
        <button class="link" @click=${()=>this.dispatchEvent(new CustomEvent("open-monitor",{detail:t.id}))}>
          ${e("open_monitor")}
        </button>
      </div>
      <div class="row">
        <span class="chip ${t.available?ne[n]??"":"bad"}">${this.stateLabel(t)}</span>
        ${null!=i.tx_error_counter?W`<span class="muted">${e("tec_rec")} ${i.tx_error_counter} / ${i.rx_error_counter}</span>`:K}
        ${t.recording?W`<span class="chip bad">● ${e("recording_now",{name:t.recording.name,n:t.recording.frames})}</span>`:K}
      </div>
      ${this.hints(t).map(t=>W`<div class="hint ${t.cls}">${t.text}</div>`)}
      ${t.virtual?K:W`<div>
            <div class="row">
              <span>${e("load")}</span><span class="grow"></span>
              <b>${Pt(s.now)}</b>
            </div>
            <div class="bar ${(s.now??0)>70?"hot":""}" title=${e("load_hint")}>
              <i style="width:${Math.min(100,s.now??0)}%"></i>
            </div>
            <div class="muted" style="margin-top:4px">
              ${e("load_values",{now:Pt(s.now),peak:Pt(s.peak),a1:Pt(s.avg[0]),a5:Pt(s.avg[1]),a15:Pt(s.avg[2])})}
            </div>
            ${this.sparkline(this.history[t.id]??[])}
          </div>`}
      <dl>
        <dt>${e("traffic")}</dt>
        <dd>${e("rates",{rx:(s.rx_fps??0).toFixed(1),tx:(s.tx_fps??0).toFixed(1)})}</dd>
        <dt>${e("seen")}</dt>
        <dd>${e("ids_seen",{n:t.monitor.ids,f:t.monitor.frames.toLocaleString()})}</dd>
        ${t.virtual?K:W`<dt>${e("controller_events")}</dt>
              <dd>${i.error_warning??"–"} / ${i.error_passive??"–"} / ${i.bus_off??"–"} / ${i.restarts??"–"}</dd>
              <dt>${e("bus_errors")}</dt>
              <dd>${r}</dd>`}
        <dt>${e("drops")}</dt>
        <dd>${i.socket_drops??0} / ${i.rx_over_errors??0} / ${i.events_dropped??0}</dd>
        <dt>${e("last_error")}</dt>
        <dd>
          ${a?W`<span title=${`${Nt(a.t)} · ${a.frame}`}
                >${a.codes.map(t=>function(t,e){const i=`err_${t}`;return Dt(i)?e(i):t}(t,e)).join("、")} · ${It(a.t,e)}</span
              >`:e("none")}
        </dd>
      </dl>
      <div class="muted">
        ${t.settings.event_filter?e("events_filter",{x:t.settings.event_filter}):e("events_none")}
        ${i.clock?W` · ${e("clock_mhz",{n:Number(i.clock)/1e6})}`:K}
        ${i.sample_point?W` · ${e("sample_point",{n:(100*Number(i.sample_point)).toFixed(1)})}`:K}
      </div>
    </div>`}render(){return this.interfaces.length?W`<div class="cards">${this.interfaces.map(t=>this.card(t))}</div>`:W`<div class="card"><div class="empty">${this.t("no_interfaces")}</div></div>`}}ce.styles=[Ot,a`
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
    `],t([ut({attribute:!1})],ce.prototype,"interfaces",void 0),t([ut({attribute:!1})],ce.prototype,"history",void 0),t([ut({attribute:!1})],ce.prototype,"t",void 0),xt("woow-can-overview",ce);const de=t=>t.target.value;class le extends dt{constructor(){super(...arguments),this.interfaces=[],this.periodic=[],this.confirmed=new Set,this.draft=null,this.entryId="",this.frame="",this.waitId="",this.waitMs=0,this.busy=!1,this.result=null,this.confirming=!1,this.edit=null,this.editError="",this.listError="",this.draftSeen=0}willUpdate(t){t.has("draft")&&this.draft&&this.draft.n!==this.draftSeen&&(this.draftSeen=this.draft.n,this.frame=this.draft.frame,this.draft.entryId&&(this.entryId=this.draft.entryId),this.result=null),this.entryId&&this.interfaces.some(t=>t.id===this.entryId)||(this.entryId=(this.interfaces.find(t=>t.can_send)??this.interfaces[0])?.id??"")}get iface(){return this.interfaces.find(t=>t.id===this.entryId)}whyNot(t){return t?t.available?t.can_send?"":this.t("why_listen"):this.t("why_unavailable"):""}trySend(){this.frame.trim()&&this.iface&&(this.confirmed.has(this.entryId)?this.send():this.confirming=!0)}async send(){const t=this.t;this.confirming=!1,this.dispatchEvent(new CustomEvent("confirmed",{detail:this.entryId})),this.busy=!0,this.result=null;try{const e=await this.api.send(this.entryId,this.frame.trim(),this.waitMs,this.waitId.trim());let i=t("sent_ok",{frame:e.sent.frame});(this.waitMs>0||this.waitId)&&(i+="\n"+(e.reply?t("reply",{frame:e.reply.frame}):t("no_reply"))),this.result={ok:!0,text:i}}catch(e){this.result={ok:!1,text:t("error",{msg:wt(e)})}}finally{this.busy=!1}}newDraft(){this.editError="",this.edit={name:"",entry_id:this.entryId,frame:this.frame.trim(),period_ms:1e3,count:0}}async saveDraft(){if(this.edit)try{await this.api.savePeriodic(this.edit),this.edit=null,this.editError=""}catch(t){this.editError=wt(t)}}async control(t,e){this.listError="";try{await this.api.controlPeriodic(t.id,e)}catch(e){this.listError=`${t.name}: ${wt(e)}`}}state(t){const e=this.t;return t.running?e("running"):"count"===t.stopped_by?e("stopped_by_count"):"error"===t.stopped_by?e("stopped_by_error",{x:t.error??"?"}):"interface"===t.stopped_by?e("stopped_by_interface"):e("stopped")}renderEditor(){const t=this.t,e=this.edit;if(!e)return K;const i=t=>this.edit={...e,...t};return W`<div class="editor">
      <label>${t("name")}<input .value=${e.name} @input=${t=>i({name:de(t)})} /></label>
      <label>${t("interface")}
        <select @change=${t=>i({entry_id:de(t)})}>
          ${this.interfaces.map(t=>W`<option value=${t.id} ?selected=${t.id===e.entry_id}>${t.name}</option>`)}
        </select>
      </label>
      <label>${t("frame")}<input class="mono" placeholder=${t("frame_ph")} .value=${e.frame}
        @input=${t=>i({frame:de(t)})} /></label>
      <label>${t("period_ms")}<input type="number" min="10" .value=${String(e.period_ms)}
        @input=${t=>i({period_ms:Number(de(t))})} /></label>
      <label>${t("count")}<input type="number" min="0" .value=${String(e.count)}
        @input=${t=>i({count:Number(de(t))})} /></label>
      <div class="row">
        <button class="primary" @click=${()=>this.saveDraft()}>${t("save")}</button>
        <button @click=${()=>this.edit=null}>${t("cancel")}</button>
      </div>
      ${this.editError?W`<div class="chip bad" style="white-space:normal">${this.editError}</div>`:K}
    </div>`}render(){const t=this.t,e=this.iface,i=this.whyNot(e),s=t=>this.interfaces.find(e=>e.id===t)?.name??"?";return W`<div class="card">
        <h2>${t("send_title")}</h2>
        <div class="form">
          <label>${t("interface")}
            <select @change=${t=>this.entryId=de(t)}>
              ${this.interfaces.map(e=>W`<option value=${e.id} ?selected=${e.id===this.entryId}>
                ${e.name}${e.can_send?"":` (${t("listen_only")})`}</option>`)}
            </select>
          </label>
          <label class="wide">${t("frame")}
            <input class="mono" placeholder=${t("frame_ph")} .value=${this.frame}
              @input=${t=>this.frame=de(t)}
              @keydown=${t=>"Enter"===t.key&&this.trySend()} />
          </label>
          <label>${t("wait_id")}<input class="mono" placeholder="7E8" .value=${this.waitId}
            @input=${t=>this.waitId=de(t)} /></label>
          <label>${t("wait_ms")}<input type="number" min="0" step="100" .value=${String(this.waitMs)}
            @input=${t=>this.waitMs=Math.max(0,Number(de(t))||0)} /></label>
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
                  <td>${s(e.entry_id)}</td>
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
          </div>`:K}`}}le.styles=[Ot,a`
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
    `],t([ut({attribute:!1})],le.prototype,"interfaces",void 0),t([ut({attribute:!1})],le.prototype,"periodic",void 0),t([ut({attribute:!1})],le.prototype,"confirmed",void 0),t([ut({attribute:!1})],le.prototype,"draft",void 0),t([ut({attribute:!1})],le.prototype,"t",void 0),t([ut({attribute:!1})],le.prototype,"api",void 0),t([mt()],le.prototype,"entryId",void 0),t([mt()],le.prototype,"frame",void 0),t([mt()],le.prototype,"waitId",void 0),t([mt()],le.prototype,"waitMs",void 0),t([mt()],le.prototype,"busy",void 0),t([mt()],le.prototype,"result",void 0),t([mt()],le.prototype,"confirming",void 0),t([mt()],le.prototype,"edit",void 0),t([mt()],le.prototype,"editError",void 0),t([mt()],le.prototype,"listError",void 0),xt("woow-can-send",le);const he=["overview","monitor","devices","send","capture","activity"];class pe extends dt{constructor(){super(...arguments),this.narrow=!1,this.tab=kt("woow_can.tab","overview"),this.interfaces={},this.offline=[],this.periodic={},this.activity=[],this.files=[],this.history={},this.source=kt("woow_can.source",""),this.draft=null,this.devices={},this.values={},this.signalHistory={},this.charts=kt("woow_can.charts",[]),this.templates=[],this.databases=[],this.confirmed=new Set,this.loaded=!1,this.error="",this.t=Ct("en"),this.api=new yt(()=>this._hass),this.connecting=!1}set hass(t){const e=!this._hass;this._hass=t,e&&(this.t=Ct(t.locale?.language??t.language??"en"),this.isConnected&&this.connect(),this.requestUpdate())}get hass(){return this._hass}connectedCallback(){super.connectedCallback(),this._hass&&!this.unsubscribe&&this.connect()}disconnectedCallback(){super.disconnectedCallback(),this.unsubscribe?.(),this.unsubscribe=void 0}async connect(){if(!this.connecting&&!this.unsubscribe){this.connecting=!0;try{this.unsubscribe=await this.api.subscribe(t=>this.onEvent(t));const t=await this.api.snapshot();this.interfaces=Object.fromEntries(t.interfaces.map(t=>[t.id,t])),this.offline=t.offline,this.periodic=Object.fromEntries(t.periodic.map(t=>[t.id,t])),this.activity=t.activity,this.devices=Object.fromEntries((t.devices??[]).map(t=>[t.id,t])),this.values=t.values??{},this.templates=t.templates??[],this.databases=t.databases??[],this.source&&(this.source in this.interfaces||t.offline.some(t=>t.id===this.source))||(this.source=this.interfaceList[0]?.id??""),this.loaded=!0,this.error="",this.loadFiles()}catch(t){this.error=wt(t)}finally{this.connecting=!1}}}async loadFiles(){try{const t=await this.api.captures();this.files=t.captures,this.offline=t.offline}catch{}}onEvent(t){switch(t.kind){case"interfaces":{const e={...this.interfaces},i={...this.history};for(const s of t.interfaces)e[s.id]=s,null!=s.load.now&&(i[s.id]=[...i[s.id]??[],s.load.now].slice(-300));for(const i of t.removed)delete e[i];this.interfaces=e,this.history=i,!this.source&&t.interfaces.length&&(this.source=t.interfaces[0].id);break}case"periodic":{const e={...this.periodic};for(const i of t.items)e[i.id]=i;for(const i of t.removed)delete e[i];this.periodic=e;break}case"activity":this.activity=[...t.entries.reverse(),...this.activity].slice(0,500);break;case"captures":this.loadFiles();break;case"devices":{const e={...this.devices};for(const i of t.devices)e[i.id]=i;for(const i of t.removed)delete e[i];this.devices=e;break}case"values":{const e={...this.values},i={...this.signalHistory};for(const[s,r]of Object.entries(t.values)){e[s]={...e[s]??{},...r};for(const[e,o]of Object.entries(r)){if("number"!=typeof o)continue;const r=`${s}|${e}`;i[r]=[...i[r]??[],[t.t,o]].slice(-300)}}this.values=e,this.signalHistory=i;break}case"databases":this.databases=t.databases;break;case"offline":this.offline=t.offline,this.source.startsWith("file:")&&!t.offline.some(t=>t.id===this.source)&&(this.source=this.interfaceList[0]?.id??"")}}get interfaceList(){return Object.values(this.interfaces).sort((t,e)=>t.name.localeCompare(e.name))}setTab(t){this.tab=t,At("woow_can.tab",t)}setSource(t){this.source=t,At("woow_can.source",t)}toggleMenu(){this.dispatchEvent(new Event("hass-toggle-menu",{bubbles:!0,composed:!0}))}renderTab(){const t=this.interfaceList;switch(this.tab){case"monitor":return W`<woow-can-monitor
          .interfaces=${t}
          .offline=${this.offline}
          .source=${this.source}
          .t=${this.t}
          .api=${this.api}
          @source-changed=${t=>this.setSource(t.detail)}
          @send-frame=${t=>{this.draft={...t.detail,n:(this.draft?.n??0)+1},this.setTab("send")}}
        ></woow-can-monitor>`;case"devices":return W`<woow-can-devices
          .interfaces=${t}
          .devices=${Object.values(this.devices).sort((t,e)=>t.name.localeCompare(e.name))}
          .values=${this.values}
          .history=${this.signalHistory}
          .charts=${this.charts}
          .templates=${this.templates}
          .databases=${this.databases}
          .preferredInterface=${this.source}
          .t=${this.t}
          .api=${this.api}
          @toggle-chart=${t=>{const e=this.charts.includes(t.detail)?this.charts.filter(e=>e!==t.detail):[...this.charts,t.detail].slice(-8);this.charts=e,At("woow_can.charts",e)}}
        ></woow-can-devices>`;case"send":return W`<woow-can-send
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
        ></woow-can-overview>`}}render(){const t=this.t,e={devices:Object.keys(this.devices).length,send:Object.values(this.periodic).filter(t=>t.running).length,capture:this.files.length};return W`
      <div class="toolbar">
        ${this.narrow?W`<button @click=${this.toggleMenu} aria-label="menu">
              <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d=${"M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z"}></path></svg>
            </button>`:K}
        <div>${t("title")}</div>
      </div>
      <div class="tabs">
        ${he.map(i=>W`<button class="tab ${this.tab===i?"active":""}" @click=${()=>this.setTab(i)}>
            ${t(`tab_${i}`)}${e[i]?W`<span class="count">${e[i]}</span>`:K}
          </button>`)}
      </div>
      <div class="content">
        ${this.error?W`<div class="card"><div class="chip bad">${t("error",{msg:this.error})}</div></div>`:this.loaded?this.renderTab():W`<div class="empty">${t("loading")}</div>`}
      </div>
    `}}pe.styles=[Ot,a`
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
    `],t([ut({attribute:!1})],pe.prototype,"narrow",void 0),t([ut({attribute:!1})],pe.prototype,"route",void 0),t([ut({attribute:!1})],pe.prototype,"panel",void 0),t([mt()],pe.prototype,"tab",void 0),t([mt()],pe.prototype,"interfaces",void 0),t([mt()],pe.prototype,"offline",void 0),t([mt()],pe.prototype,"periodic",void 0),t([mt()],pe.prototype,"activity",void 0),t([mt()],pe.prototype,"files",void 0),t([mt()],pe.prototype,"history",void 0),t([mt()],pe.prototype,"source",void 0),t([mt()],pe.prototype,"draft",void 0),t([mt()],pe.prototype,"devices",void 0),t([mt()],pe.prototype,"values",void 0),t([mt()],pe.prototype,"signalHistory",void 0),t([mt()],pe.prototype,"charts",void 0),t([mt()],pe.prototype,"templates",void 0),t([mt()],pe.prototype,"databases",void 0),t([mt()],pe.prototype,"confirmed",void 0),t([mt()],pe.prototype,"loaded",void 0),t([mt()],pe.prototype,"error",void 0),xt("woow-can-panel",pe);export{pe as WoowCanPanel};
