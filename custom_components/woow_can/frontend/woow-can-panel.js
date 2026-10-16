function t(t,e,i,s){var a,r=arguments.length,o=r<3?e:null===s?s=Object.getOwnPropertyDescriptor(e,i):s;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)o=Reflect.decorate(t,e,i,s);else for(var n=t.length-1;n>=0;n--)(a=t[n])&&(o=(r<3?a(o):r>3?a(e,i,o):a(e,i))||o);return r>3&&o&&Object.defineProperty(e,i,o),o}"function"==typeof SuppressedError&&SuppressedError;const e=globalThis,i=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s=Symbol(),a=new WeakMap;let r=class{constructor(t,e,i){if(this._$cssResult$=!0,i!==s)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const e=this.t;if(i&&void 0===t){const i=void 0!==e&&1===e.length;i&&(t=a.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),i&&a.set(e,t))}return t}toString(){return this.cssText}};const o=(t,...e)=>{const i=1===t.length?t[0]:e.reduce((e,i,s)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+t[s+1],t[0]);return new r(i,t,s)},n=i?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const i of t.cssRules)e+=i.cssText;return(t=>new r("string"==typeof t?t:t+"",void 0,s))(e)})(t):t,{is:c,defineProperty:l,getOwnPropertyDescriptor:d,getOwnPropertyNames:h,getOwnPropertySymbols:p,getPrototypeOf:u}=Object,m=globalThis,f=m.trustedTypes,_=f?f.emptyScript:"",v=m.reactiveElementPolyfillSupport,g=(t,e)=>t,b={toAttribute(t,e){switch(e){case Boolean:t=t?_:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let i=t;switch(e){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t)}catch(t){i=null}}return i}},$=(t,e)=>!c(t,e),y={attribute:!0,type:String,converter:b,reflect:!1,useDefault:!1,hasChanged:$};Symbol.metadata??=Symbol("metadata"),m.litPropertyMetadata??=new WeakMap;let w=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=y){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const i=Symbol(),s=this.getPropertyDescriptor(t,i,e);void 0!==s&&l(this.prototype,t,s)}}static getPropertyDescriptor(t,e,i){const{get:s,set:a}=d(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:s,set(e){const r=s?.call(this);a?.call(this,e),this.requestUpdate(t,r,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??y}static _$Ei(){if(this.hasOwnProperty(g("elementProperties")))return;const t=u(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(g("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(g("properties"))){const t=this.properties,e=[...h(t),...p(t)];for(const i of e)this.createProperty(i,t[i])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,i]of e)this.elementProperties.set(t,i)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const i=this._$Eu(t,e);void 0!==i&&this._$Eh.set(i,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const i=new Set(t.flat(1/0).reverse());for(const t of i)e.unshift(n(t))}else void 0!==t&&e.push(n(t));return e}static _$Eu(t,e){const i=e.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((t,s)=>{if(i)t.adoptedStyleSheets=s.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const i of s){const s=document.createElement("style"),a=e.litNonce;void 0!==a&&s.setAttribute("nonce",a),s.textContent=i.cssText,t.appendChild(s)}})(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){const i=this.constructor.elementProperties.get(t),s=this.constructor._$Eu(t,i);if(void 0!==s&&!0===i.reflect){const a=(void 0!==i.converter?.toAttribute?i.converter:b).toAttribute(e,i.type);this._$Em=t,null==a?this.removeAttribute(s):this.setAttribute(s,a),this._$Em=null}}_$AK(t,e){const i=this.constructor,s=i._$Eh.get(t);if(void 0!==s&&this._$Em!==s){const t=i.getPropertyOptions(s),a="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:b;this._$Em=s;const r=a.fromAttribute(e,t.type);this[s]=r??this._$Ej?.get(s)??r,this._$Em=null}}requestUpdate(t,e,i,s=!1,a){if(void 0!==t){const r=this.constructor;if(!1===s&&(a=this[t]),i??=r.getPropertyOptions(t),!((i.hasChanged??$)(a,e)||i.useDefault&&i.reflect&&a===this._$Ej?.get(t)&&!this.hasAttribute(r._$Eu(t,i))))return;this.C(t,e,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:s,wrapped:a},r){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,r??e??this[t]),!0!==a||void 0!==r)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),!0===s&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,i]of t){const{wrapped:t}=i,s=this[e];!0!==t||this._$AL.has(e)||void 0===s||this.C(e,void 0,i,s)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};w.elementStyles=[],w.shadowRootOptions={mode:"open"},w[g("elementProperties")]=new Map,w[g("finalized")]=new Map,v?.({ReactiveElement:w}),(m.reactiveElementVersions??=[]).push("2.1.2");const x=globalThis,k=t=>t,S=x.trustedTypes,A=S?S.createPolicy("lit-html",{createHTML:t=>t}):void 0,C="$lit$",E=`lit$${Math.random().toFixed(9).slice(2)}$`,D="?"+E,I=`<${D}>`,N=document,M=()=>N.createComment(""),T=t=>null===t||"object"!=typeof t&&"function"!=typeof t,z=Array.isArray,O="[ \t\n\f\r]",P=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,R=/-->/g,F=/>/g,B=RegExp(`>|${O}(?:([^\\s"'>=/]+)(${O}*=${O}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),U=/'/g,H=/"/g,j=/^(?:script|style|textarea|title)$/i,W=t=>(e,...i)=>({_$litType$:t,strings:e,values:i}),L=W(1),V=W(2),q=Symbol.for("lit-noChange"),K=Symbol.for("lit-nothing"),G=new WeakMap,J=N.createTreeWalker(N,129);function Z(t,e){if(!z(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==A?A.createHTML(e):e}class X{constructor({strings:t,_$litType$:e},i){let s;this.parts=[];let a=0,r=0;const o=t.length-1,n=this.parts,[c,l]=((t,e)=>{const i=t.length-1,s=[];let a,r=2===e?"<svg>":3===e?"<math>":"",o=P;for(let e=0;e<i;e++){const i=t[e];let n,c,l=-1,d=0;for(;d<i.length&&(o.lastIndex=d,c=o.exec(i),null!==c);)d=o.lastIndex,o===P?"!--"===c[1]?o=R:void 0!==c[1]?o=F:void 0!==c[2]?(j.test(c[2])&&(a=RegExp("</"+c[2],"g")),o=B):void 0!==c[3]&&(o=B):o===B?">"===c[0]?(o=a??P,l=-1):void 0===c[1]?l=-2:(l=o.lastIndex-c[2].length,n=c[1],o=void 0===c[3]?B:'"'===c[3]?H:U):o===H||o===U?o=B:o===R||o===F?o=P:(o=B,a=void 0);const h=o===B&&t[e+1].startsWith("/>")?" ":"";r+=o===P?i+I:l>=0?(s.push(n),i.slice(0,l)+C+i.slice(l)+E+h):i+E+(-2===l?e:h)}return[Z(t,r+(t[i]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),s]})(t,e);if(this.el=X.createElement(c,i),J.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(s=J.nextNode())&&n.length<o;){if(1===s.nodeType){if(s.hasAttributes())for(const t of s.getAttributeNames())if(t.endsWith(C)){const e=l[r++],i=s.getAttribute(t).split(E),o=/([.?@])?(.*)/.exec(e);n.push({type:1,index:a,name:o[2],strings:i,ctor:"."===o[1]?it:"?"===o[1]?st:"@"===o[1]?at:et}),s.removeAttribute(t)}else t.startsWith(E)&&(n.push({type:6,index:a}),s.removeAttribute(t));if(j.test(s.tagName)){const t=s.textContent.split(E),e=t.length-1;if(e>0){s.textContent=S?S.emptyScript:"";for(let i=0;i<e;i++)s.append(t[i],M()),J.nextNode(),n.push({type:2,index:++a});s.append(t[e],M())}}}else if(8===s.nodeType)if(s.data===D)n.push({type:2,index:a});else{let t=-1;for(;-1!==(t=s.data.indexOf(E,t+1));)n.push({type:7,index:a}),t+=E.length-1}a++}}static createElement(t,e){const i=N.createElement("template");return i.innerHTML=t,i}}function Q(t,e,i=t,s){if(e===q)return e;let a=void 0!==s?i._$Co?.[s]:i._$Cl;const r=T(e)?void 0:e._$litDirective$;return a?.constructor!==r&&(a?._$AO?.(!1),void 0===r?a=void 0:(a=new r(t),a._$AT(t,i,s)),void 0!==s?(i._$Co??=[])[s]=a:i._$Cl=a),void 0!==a&&(e=Q(t,a._$AS(t,e.values),a,s)),e}class Y{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:i}=this._$AD,s=(t?.creationScope??N).importNode(e,!0);J.currentNode=s;let a=J.nextNode(),r=0,o=0,n=i[0];for(;void 0!==n;){if(r===n.index){let e;2===n.type?e=new tt(a,a.nextSibling,this,t):1===n.type?e=new n.ctor(a,n.name,n.strings,this,t):6===n.type&&(e=new rt(a,this,t)),this._$AV.push(e),n=i[++o]}r!==n?.index&&(a=J.nextNode(),r++)}return J.currentNode=N,s}p(t){let e=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}}class tt{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,i,s){this.type=2,this._$AH=K,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=Q(this,t,e),T(t)?t===K||null==t||""===t?(this._$AH!==K&&this._$AR(),this._$AH=K):t!==this._$AH&&t!==q&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>z(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==K&&T(this._$AH)?this._$AA.nextSibling.data=t:this.T(N.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:i}=t,s="number"==typeof i?this._$AC(t):(void 0===i.el&&(i.el=X.createElement(Z(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===s)this._$AH.p(e);else{const t=new Y(s,this),i=t.u(this.options);t.p(e),this.T(i),this._$AH=t}}_$AC(t){let e=G.get(t.strings);return void 0===e&&G.set(t.strings,e=new X(t)),e}k(t){z(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let i,s=0;for(const a of t)s===e.length?e.push(i=new tt(this.O(M()),this.O(M()),this,this.options)):i=e[s],i._$AI(a),s++;s<e.length&&(this._$AR(i&&i._$AB.nextSibling,s),e.length=s)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=k(t).nextSibling;k(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class et{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,s,a){this.type=1,this._$AH=K,this._$AN=void 0,this.element=t,this.name=e,this._$AM=s,this.options=a,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=K}_$AI(t,e=this,i,s){const a=this.strings;let r=!1;if(void 0===a)t=Q(this,t,e,0),r=!T(t)||t!==this._$AH&&t!==q,r&&(this._$AH=t);else{const s=t;let o,n;for(t=a[0],o=0;o<a.length-1;o++)n=Q(this,s[i+o],e,o),n===q&&(n=this._$AH[o]),r||=!T(n)||n!==this._$AH[o],n===K?t=K:t!==K&&(t+=(n??"")+a[o+1]),this._$AH[o]=n}r&&!s&&this.j(t)}j(t){t===K?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class it extends et{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===K?void 0:t}}class st extends et{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==K)}}class at extends et{constructor(t,e,i,s,a){super(t,e,i,s,a),this.type=5}_$AI(t,e=this){if((t=Q(this,t,e,0)??K)===q)return;const i=this._$AH,s=t===K&&i!==K||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,a=t!==K&&(i===K||s);s&&this.element.removeEventListener(this.name,this,i),a&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class rt{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){Q(this,t)}}const ot={I:tt},nt=x.litHtmlPolyfillSupport;nt?.(X,tt),(x.litHtmlVersions??=[]).push("3.3.3");const ct=globalThis;let lt=class extends w{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,i)=>{const s=i?.renderBefore??e;let a=s._$litPart$;if(void 0===a){const t=i?.renderBefore??null;s._$litPart$=a=new tt(e.insertBefore(M(),t),t,void 0,i??{})}return a._$AI(t),a})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return q}};lt._$litElement$=!0,lt.finalized=!0,ct.litElementHydrateSupport?.({LitElement:lt});const dt=ct.litElementPolyfillSupport;dt?.({LitElement:lt}),(ct.litElementVersions??=[]).push("4.2.2");const ht={attribute:!0,type:String,converter:b,reflect:!1,hasChanged:$},pt=(t=ht,e,i)=>{const{kind:s,metadata:a}=i;let r=globalThis.litPropertyMetadata.get(a);if(void 0===r&&globalThis.litPropertyMetadata.set(a,r=new Map),"setter"===s&&((t=Object.create(t)).wrapped=!0),r.set(i.name,t),"accessor"===s){const{name:s}=i;return{set(i){const a=e.get.call(this);e.set.call(this,i),this.requestUpdate(s,a,t,!0,i)},init(e){return void 0!==e&&this.C(s,void 0,t,e),e}}}if("setter"===s){const{name:s}=i;return function(i){const a=this[s];e.call(this,i),this.requestUpdate(s,a,t,!0,i)}}throw Error("Unsupported decorator location: "+s)};function ut(t){return(e,i)=>"object"==typeof i?pt(t,e,i):((t,e,i)=>{const s=e.hasOwnProperty(i);return e.constructor.createProperty(i,t),s?Object.getOwnPropertyDescriptor(e,i):void 0})(t,e,i)}function mt(t){return ut({...t,state:!0,attribute:!1})}const ft=["log","asc","csv","pcap"];function _t(t,e,i){if("little"===i)return{start:Math.min(t,e),length:Math.abs(t-e)+1};const s=t=>8*Math.floor(t/8)+(7-t%8),[a,r]=s(t)<=s(e)?[t,e]:[e,t];return{start:a,length:s(r)-s(a)+1}}const vt=2**32;function gt(t){return Math.floor(t/2147483648)%2==1}function bt(t){const e=t%536870912;return gt(t)?e.toString(16).toUpperCase().padStart(8,"0"):(e%2048).toString(16).toUpperCase().padStart(3,"0")}function $t(t,e,i){if(16&e)return`${(536870912+t%536870912).toString(16).toUpperCase().padStart(8,"0")}#${i}`;const s=bt(t);return!function(t){return Math.floor(t/1073741824)%2==1}(t)||1&e?1&e?`${s}##${2&e?1:0}${i}`:`${s}#${i}`:`${s}#R`}class yt{constructor(t){this.exact=new Set,this.masks=[],this.ranges=[],this.error="";let e=!t.trim(),i="";for(const s of t.split(/[,;]/)){const t=s.trim();if(t)if("*"!==t)try{if(t.includes("-")){const[e,i]=t.split("-"),[s,a]=wt(e),[r,o]=wt(i);if(r<s)throw new Error(t);this.ranges.push([s,r,a||o])}else if(t.includes("/")){const[e,i]=t.split("/"),[s,a]=wt(e);this.masks.push([s,wt(i)[0],a])}else{const[e,i]=wt(t);this.exact.add(`${i?"x":""}${e}`)}}catch{i=t}else e=!0}this.all=e,this.error=i}matches(t){if(this.all)return!0;const e=gt(t),i=e?t%536870912:t%2048;if(this.exact.has(`${e?"x":""}${i}`))return!0;for(const[t,s,a]of this.masks)if(a===e&&(i&s)===(t&s))return!0;for(const[t,s,a]of this.ranges)if(a===e&&i>=t&&i<=s)return!0;return!1}}function wt(t){let e=t.trim();if(e.toLowerCase().startsWith("0x")&&(e=e.slice(2)),!/^[0-9a-fA-F]{1,8}$/.test(e))throw new Error(`bad CAN ID ${t}`);const i=parseInt(e,16);if(i>536870911)throw new Error(`CAN ID ${t} is out of range`);return[i,e.length>3||i>2047]}class xt{constructor(t){this.hass=t}subscribe(t){return this.hass().connection.subscribeMessage(t,{type:"woow_can/subscribe"})}snapshot(){return this.hass().callWS({type:"woow_can/snapshot"})}subscribeMonitor(t,e,i){return this.hass().connection.subscribeMessage(i,{type:"woow_can/monitor/subscribe",source:t,token:e})}ack(t,e){return this.hass().callWS({type:"woow_can/monitor/ack",token:t,seq:e})}clearMonitor(t){return this.hass().callWS({type:"woow_can/monitor/clear",source:t})}trace(t,e){return this.hass().callWS({type:"woow_can/trace",source:t,limit:e.limit??200,ids:e.ids??"",...null!=e.before?{before:e.before}:{},...e.direction?{direction:e.direction}:{}})}send(t,e,i=0,s=""){return this.hass().callWS({type:"woow_can/send",entry_id:t,frame:e,wait_ms:i,...s?{wait_id:s}:{}})}setEvents(t,e){return this.hass().callWS({type:"woow_can/interface/events",entry_id:t,event_filter:e})}savePeriodic(t){return this.hass().callWS({type:"woow_can/periodic/save",item:t})}controlPeriodic(t,e){return this.hass().callWS({type:"woow_can/periodic/control",item_id:t,action:e})}captures(){return this.hass().callWS({type:"woow_can/capture/list"})}capture(t,e){return this.hass().callWS({type:"woow_can/capture/control",action:t,...e})}analyzeBits(t,e,i){return this.hass().callWS({type:"woow_can/analyze/bits",source:t,key:e,limit:2e3,...i?{seconds:i}:{}})}analyzeTry(t,e,i,s){return this.hass().callWS({type:"woow_can/analyze/try",source:t,key:e,signal:i,limit:2e3,...s?{seconds:s}:{}})}analyzeFind(t,e,i={}){const s={};return i.mode&&(s.mode=i.mode),null!=i.value&&(s.value=i.value),null!=i.tolerance&&(s.tolerance=i.tolerance),this.hass().callWS({type:"woow_can/analyze/find",source:t,action:e,limit:30,...s})}analyzeGuided(t,e,i){return this.hass().callWS({type:"woow_can/analyze/guided",source:t,action:e,...i?{label:i}:{}})}addSignal(t,e,i,s,a=!0){return this.hass().callWS({type:"woow_can/devices/add_signal",entry_id:t,key:e,signal:i,adopt:a,...s})}saveDevice(t){return this.hass().callWS({type:"woow_can/devices/save",device:t})}deleteDevice(t){return this.hass().callWS({type:"woow_can/devices/delete",device_id:t})}setSignal(t,e,i,s){return this.hass().callWS({type:"woow_can/devices/signal",device_id:t,message:e,signal:i,...s})}createFromTemplate(t,e,i,s,a){return this.hass().callWS({type:"woow_can/templates/create",template:t,entry_id:e,name:i,params:s,groups:a})}decode(t,e,i){return this.hass().callWS({type:"woow_can/decode",source:t,raw:e,data:i})}dbc(t,e,i={}){return this.hass().callWS({type:"woow_can/dbc/control",action:t,name:e,...i})}async uploadDbc(t,e){const i=`name=${encodeURIComponent(t.name)}${e.length?`&attach=${encodeURIComponent(e.join(","))}`:""}`,s=await this.hass().fetchWithAuth(`/api/woow_can/dbc?${i}`,{method:"POST",body:t});if(!s.ok)throw new Error(`${s.status} ${await s.text()}`);return await s.json()}async download(t){const e=await this.hass().callWS({type:"auth/sign_path",path:t,expires:60}),i=document.createElement("a");i.href=this.hass().hassUrl(e.path),i.download="",document.body.appendChild(i),i.click(),i.remove()}async upload(t){const e=await this.hass().fetchWithAuth(`/api/woow_can/captures?name=${encodeURIComponent(t.name)}`,{method:"POST",body:t});if(!e.ok)throw new Error(`${e.status} ${await e.text()}`);return(await e.json()).name}}function kt(t){return String(t&&"object"==typeof t&&"message"in t?t.message:t)}function St(t,e){customElements.get(t)||customElements.define(t,e)}function At(t,e){try{const i=window.localStorage.getItem(t);return i?JSON.parse(i):e}catch{return e}}function Ct(t,e){try{window.localStorage.setItem(t,JSON.stringify(e))}catch{}}const Et={title:"WOOW CAN",tab_overview:"Overview",tab_monitor:"Monitor",tab_send:"Send",tab_capture:"Recordings",tab_activity:"Activity",loading:"Loading…",error:"Error: {msg}",cancel:"Cancel",close:"Close",save:"Save",delete:"Delete",edit:"Edit",add:"Add",start:"Start",stop:"Stop",none:"none",just_now:"just now",s_ago:"{n} s ago",m_ago:"{n} min ago",h_ago:"{n} h ago",d_ago:"{n} d ago",no_interfaces:"No CAN interfaces yet. Add one under Settings › Devices & services › WOOW CAN; without hardware, add a virtual interface to try things out.",state_error_active:"Normal",state_error_warning:"Error warning",state_error_passive:"Error passive",state_bus_off:"Bus off",state_stopped:"Stopped",state_sleeping:"Sleeping",state_virtual:"Virtual",state_unknown:"Unknown",unavailable:"Unavailable",listen_only:"listen only",can_fd:"CAN FD",kbps:"{n} kbit/s",virtual_iface:"virtual",load:"Bus load",load_values:"now {now} · peak {peak} · 1/5/15 min {a1} / {a5} / {a15}",load_hint:"Estimated with worst-case bit stuffing; it can exceed 100 %.",rates:"received {rx}/s · sent {tx}/s",traffic:"Traffic",seen:"Seen since start",tec_rec:"TEC / REC",controller_events:"Warnings / passive / bus-off / restarts",bus_errors:"Bus errors",arbitration_lost:"Arbitration lost",not_supported:"not reported by this controller",reporting_off:"reporting off",drops:"Dropped (socket / controller overflow / over the event rate)",last_error:"Last error frame",ids_seen:"{n} IDs · {f} frames",recording_now:"Recording {name} ({n} frames)",clock_mhz:"clock {n} MHz",sample_point:"sample point {n} %",events_filter:"Events for: {x}",events_none:"No events (event filter empty)",open_monitor:"Monitor",hint_passive:"Nothing on the bus acknowledges this interface's frames. Check the wiring, the 120 Ω termination at both ends and that every node uses the same bitrate.",hint_bus_off_auto:"The controller went bus-off; it restarts after {ms} ms.",hint_bus_off_manual:"The controller went bus-off and stays off: reload the interface.",hint_listen_only:"Listen only: this interface never acknowledges or sends.",hint_overflow:"The controller lost {n} frames (receive overflow): the bus is busier than it can follow.",hint_socket_drops:"{n} frames were dropped before Home Assistant read them.",sparkline:"Load over the last minutes","err_controller:rx_overflow":"receive overflow","err_controller:tx_overflow":"transmit overflow","err_controller:rx_warning":"receive errors at warning level","err_controller:tx_warning":"transmit errors at warning level","err_controller:rx_passive":"receive error passive","err_controller:tx_passive":"transmit error passive","err_controller:active":"back to error active",err_controller:"controller problem","err_protocol:bit":"bit error","err_protocol:form":"form error","err_protocol:stuff":"stuff error","err_protocol:bit0":"could not send a dominant bit","err_protocol:bit1":"could not send a recessive bit","err_protocol:overload":"bus overload","err_protocol:active_error":"active error flag","err_protocol:on_tx":"while transmitting",err_protocol:"protocol error",err_tx_timeout:"transmit timeout",err_lost_arbitration:"lost arbitration",err_transceiver:"transceiver problem",err_no_ack:"no acknowledgement",err_bus_off:"bus off",err_bus_error:"bus error",err_restarted:"controller restarted",source:"Source",file_source:"{name} (file)",pause:"Pause",resume:"Resume",clear:"Clear",notch:"Notch",notch_clear:"Clear notch",changing_only:"Changing only",hide_inactive:"Hide silent > 5 s",view_hex:"HEX",view_bin:"Binary",filter_ph:"IDs: 123, 7E0/7F0, 100-1FF",filter_bad:"Not understood: {x}",col_id:"ID",col_name:"Name",col_len:"Len",col_data:"Data",col_count:"Count",col_hz:"Hz",col_period:"Period",col_dchg:"Change gap",col_age:"Age",col_time:"Time",col_dir:"Dir",dir_rx:"Rx",dir_tx:"Tx",dir_local:"this host",monitor_empty:"No frames yet. Check that the bus is connected and every node uses the same bitrate, or open a recording under Recordings.",monitor_hint:"One row per ID. A changed byte lights up and fades: cyan rising, red falling, grey-violet for bytes that keep jumping (counters, checksums). To find a signal: leave the equipment alone for 10 s, press Notch two or three times until the screen is quiet, then operate the equipment and watch which bytes light up.",notch_added:"Masked {n} bits that changed in the last 2 s.",notch_none:"No bits changed in the last 2 s.",overflow:"More than 4096 IDs: {n} further frames are only counted.",frames_total:"{ids} IDs · {n} frames",row_pin:"Pin",row_unpin:"Unpin",row_send:"Send again",row_events:"Fire events",row_events_on:"Fires events",row_trace:"In time order",row_notch:"Notch this row",detail_period:"Period {avg} ms ({min}–{max})",detail_rate:"{hz} frames/s",detail_changed:"Data last changed {ago}; gap between the last two changes {gap}",paused_title:"Paused: frames in time order, newest first",trace_older:"Older",trace_start:"That is the oldest frame in the buffer.",trace_all_dirs:"Both directions",trace_time:"Time",trace_delta:"Δ",trace_error:"error frame: {x}",trace_empty:"No frames match.",events_added:"Frames with ID {id} now fire woow_can_frame events.",gone:"The interface was reloaded; reconnecting…",offline_note:"Recording {file}: {n} frames. The monitor shows the state at the end of the file.",send_title:"Send a frame",interface:"Interface",frame:"Frame",frame_ph:"123#11223344",frame_help:"ID#data: 1–3 digit IDs are 11-bit, longer ones 29-bit; 123#R is a remote frame; ID##1data is CAN FD (1 = bit rate switch).",wait_id:"Reply ID",wait_ms:"Wait (ms)",send:"Send",sent_ok:"Sent {frame}",reply:"Reply {frame}",no_reply:"No reply (timed out)",cannot_send:"{name} cannot send: {why}",why_listen:"it is set to listen only (turn that off in the interface settings)",why_unavailable:"it is not available",confirm_title:"First send on {name}",confirm_text:"Every node on the bus receives this frame. On a vehicle, machine or battery bus, only send frames whose effect you know.",confirm_ok:"Send",periodic_title:"Periodic sends",periodic_hint:"Frames sent every N ms. After Home Assistant restarts every item is stopped.",name:"Name",period_ms:"Period (ms)",count:"Count (0 = no limit)",running:"running",stopped:"stopped",sent_n:"{n} sent",stopped_by_count:"count reached",stopped_by_error:"stopped: {x}",stopped_by_interface:"interface stopped",periodic_empty:"No periodic sends yet.",capture_title:"Record",capture_hint:"Record an interface to a candump log file (canplayer, SavvyCAN, python-can and Wireshark read it), kept in Home Assistant's config folder under woow_can/captures. Downloads and conversions also come as Vector ASC, SavvyCAN CSV or pcap.",record:"Record",stop_record:"Stop",recording:"Recording · {n} frames · {size}",export:"Download buffer",export_hint:"The last {n} frames held in memory, as a file of the chosen format.",file_format:"Format",fmt_log:"candump log",fmt_asc:"Vector ASC",fmt_csv:"SavvyCAN CSV",fmt_pcap:"pcap (Wireshark)",fmt_trc:"PEAK TRC",fmt_crtd:"OVMS CRTD",convert:"Convert",convert_hint:"Write this file as {fmt} next to it",converted:"Wrote {name} ({n} frames).",csv_note:"SavvyCAN CSV keeps classic frames only (no CAN FD, remote or error frames).",files_title:"Recordings",files_empty:"No recordings yet.",download:"Download",open:"Open",upload:"Upload a log file",upload_hint:"candump log, Vector ASC, SavvyCAN CSV, PEAK TRC, OVMS CRTD or pcap",uploaded:"Uploaded {name}.",opened:"Opened; pick it as the source on the Monitor tab.",offline_title:"Open files",truncated:"only the last {n} frames",delete_confirm:"Delete {name}?",all_channels:"All sources",channel_service:"Service / AI",channel_panel:"Panel",channel_entity:"Entity",activity_hint:"Sends and changes made by AI agents (through services) and by people (in this panel).",activity_empty:"Nothing yet.",quoted:"“{x}”",log_sent:"sent {frame} on {port}",log_send_failed:"sending {frame} on {port} failed: {error}",log_periodic_saved:"saved periodic send “{name}”: {frame} every {period} ms on {port}",log_periodic_deleted:"deleted periodic send “{name}”",log_periodic_started:"started periodic send “{name}” on {port}",log_periodic_stopped:"stopped periodic send “{name}” ({sent} sent)",log_periodic_failed:"periodic send “{name}” stopped: {error}",log_capture_started:"started recording {file} on {port}",log_capture_stopped:"stopped recording {file} ({frames} frames)",log_capture_deleted:"deleted recording {file}",log_capture_uploaded:"uploaded {file}",log_capture_converted:"converted {file} to {target} ({frames} frames)",log_monitor_cleared:"cleared the monitor of {port}",tab_devices:"Devices",devices_hint:"A device turns chosen signals of an interface into Home Assistant entities. Start from a template for known equipment, or from an imported DBC file.",devices_empty:"No devices yet. Add one from a template, or import a DBC file.",add_from_template:"From a template",import_dbc:"Import DBC",template:"Template",category_battery:"Battery",category_vehicle:"Vehicle",category_marine:"Marine",category_industrial:"Industrial",confidence:"Confidence: {x}",confidence_high:"high",confidence_medium:"medium",confidence_low:"low",verified_with:"Checked against: {x}",sources:"Sources",license_x:"License: {x}",only_listens:"Only listens, never sends",groups_title:"Message groups",groups_auto:"Detect from traffic",groups_detect_hint:"Groups whose IDs this interface has already received are included.",device_name:"Device name",create:"Create",created_device:"Created {name}.",messages_n:"{n} messages",entities_n:"{n} entities",never_seen:"never received",stale:"silent",fresh:"receiving",col_signal:"Signal",col_value:"Value",col_entity:"Entity",adopt_hint:"Checked signals are Home Assistant entities.",state_on:"on",state_off:"off",entity_disabled:"disabled",settings:"Settings",min_interval:"Minimum interval (s)",tolerance:"Tolerance",timeout_s:"Timeout (s)",apply:"Apply",delete_device_confirm:"Delete {name} and its entities?",from_x:"from {x}",chart:"Chart",charts_title:"Charts",charts_empty:"Press Chart next to a numeric signal to follow it here.",dbc_title:"DBC files",dbc_hint:"Attached to an interface, a DBC file names and decodes the monitor's rows. To get entities, make a device from some of its messages.",dbc_empty:"No DBC files yet.",dbc_attached_to:"Decodes",all_interfaces:"All interfaces",dbc_warnings:"{n} lines not understood",make_device:"Make a device",download_dbc:"Download as DBC",choose_messages:"Messages",imported_dbc:"Imported {name}: {m} messages, {s} signals.",decoded_title:"Decoded",no_definition:"No device or DBC file describes this ID.",log_device_created:"created device “{device}” on {port}",log_device_updated:"updated device “{device}” on {port}",log_device_from_template:"created device “{device}” from template {template} on {port}",log_device_from_dbc:"created device “{device}” from {file} on {port}",log_device_deleted:"deleted device “{device}”",log_device_save_failed:"could not save device “{device}”: {error}",log_signal_changed:"{device}: changed signal {signal}",tab_analyze:"Analyze",an_source:"Works on {name}, the source picked on the Monitor tab.",g_title:"Guided capture: what does an action change?",g_hint:"Start and leave the equipment idle for a few seconds. Press Next, do the action (open the door, press the button) and hold it; press Next again and undo it. Repeat two or three times for a clearer result, then Finish.",g_live_only:"A guided capture needs a live interface; pick one on the Monitor tab.",g_start:"Start",g_next_action:"Next: do the action",g_next_idle:"Next: undo it",g_finish:"Finish",g_cancel:"Cancel",g_phase:"Phase {n}: {label} · {s} s",g_do_idle:"Leave the equipment idle.",g_do_action:"Do the action now and hold it.",g_label_idle:"idle",g_label_action:"action",g_results:"What differs",g_none:"Nothing differs clearly. Hold each phase a few seconds longer, or repeat the action.",g_flip:"byte {byte} bit {bit}: {a} → {b}",g_confirmed:"every time",g_shift:"byte {byte}: {a} → {b}",g_moving:"moves during the action: bits {bits}",g_only:"only sent during the action",g_counter:"counter bits {bits}",g_make_switch:"Make a binary sensor",g_try_byte:"Try the byte",g_frames:"Frames per phase: {n}",f_title:"Find a signal by its value",f_hint:"Read a value off the equipment's display (52.3 V, 87 %), enter it and start. Let the value change, enter the new value and narrow; repeat until one or a few fields are left. Without a known value, start without one and narrow by how it moved.",f_value:"Value now",f_tolerance:"Tolerance",f_start:"Start with this value",f_start_blank:"Start without a value",f_equals:"Now equals",f_increased:"Increased",f_decreased:"Decreased",f_changed:"Changed",f_unchanged:"Unchanged",f_clear:"Clear",f_left:"{n} candidates in {ids} IDs",f_truncated:"only the likeliest are kept",f_step_start:"start",f_field:"bits {start}+{length}",f_signed:"signed",f_open_bits:"Bits",f_add:"Add to a device",b_title:"Bits of one ID",b_hint:"The colour shows how often each bit changed over the recent frames: dark = on every frame (counters, checksums), light = now and then, none = never. Tap a bit to start a field and another to end it.",b_id:"CAN ID",b_tx:"sent by WOOW CAN",b_show:"Show",b_frames:"{n} frames",b_no_frames:"No recent frames of this ID.",b_byte:"byte {n}",b_little:"little endian (Intel)",b_big:"big endian (Motorola)",b_start:"Start bit",b_length:"Length",b_factor:"Factor",b_offset:"Offset",b_unit:"Unit",b_signed:"Signed",b_try:"{n} frames · {d} values · {c} changes · {min} – {max} · now {last}",b_bit_title:"bit {i}: changed {c} times ({p} %), 1 in {o} % of frames",a_title:"Add the field to a device",a_name:"Signal name",a_device:"Device",a_new_device:"New device",a_device_name:"New device name",a_interface:"Interface",a_add:"Add",a_added:"Added {signal} to {device}.",a_name_needed:"Give the signal a name.",row_analyze:"Bits & analysis",log_signal_added:"{device}: added signal {signal}",log_dbc_imported:"imported {file} ({messages} messages)",log_dbc_attached:"{file} decodes {ports}",log_dbc_deleted:"deleted {file}"},Dt={title:"WOOW CAN",tab_overview:"總覽",tab_monitor:"監看",tab_send:"發送",tab_capture:"擷取",tab_activity:"活動",loading:"載入中…",error:"錯誤：{msg}",cancel:"取消",close:"關閉",save:"儲存",delete:"刪除",edit:"編輯",add:"新增",start:"開始",stop:"停止",none:"無",just_now:"剛剛",s_ago:"{n} 秒前",m_ago:"{n} 分鐘前",h_ago:"{n} 小時前",d_ago:"{n} 天前",no_interfaces:"還沒有 CAN 介面。請到「設定 › 裝置與服務 › WOOW CAN」新增；沒有硬體的話，可以新增虛擬介面先試用。",state_error_active:"正常",state_error_warning:"錯誤警告",state_error_passive:"錯誤被動",state_bus_off:"Bus off（已離線）",state_stopped:"已停止",state_sleeping:"休眠",state_virtual:"虛擬介面",state_unknown:"未知",unavailable:"無法使用",listen_only:"只監聽",can_fd:"CAN FD",kbps:"{n} kbit/s",virtual_iface:"虛擬",load:"匯流排負載",load_values:"目前 {now} · 峰值 {peak} · 1／5／15 分鐘 {a1}／{a5}／{a15}",load_hint:"以最壞位元填充估算，所以可能超過 100%。",rates:"收 {rx} 筆/秒 · 送 {tx} 筆/秒",traffic:"流量",seen:"啟動以來",tec_rec:"TEC／REC",controller_events:"錯誤警告／錯誤被動／Bus off／重啟",bus_errors:"匯流排錯誤",arbitration_lost:"仲裁失敗",not_supported:"這顆控制器不回報",reporting_off:"未開啟回報",drops:"丟包（socket／控制器溢位／超過事件速率）",last_error:"最後一筆錯誤訊框",ids_seen:"{n} 個 ID · {f} 筆",recording_now:"錄製中：{name}（{n} 筆）",clock_mhz:"時脈 {n} MHz",sample_point:"取樣點 {n}%",events_filter:"觸發事件：{x}",events_none:"不觸發事件（事件 ID 空白）",open_monitor:"監看",hint_passive:"送出的訊框沒有任何節點回應確認（ACK）。請檢查接線、兩端的 120 Ω 終端電阻，以及所有節點的速率是否一致。",hint_bus_off_auto:"控制器進入 bus off，{ms} ms 後會自動重啟。",hint_bus_off_manual:"控制器進入 bus off，不會自動恢復：請重新載入這個介面。",hint_listen_only:"只監聽：這個介面不回 ACK，也不能發送。",hint_overflow:"控制器漏收了 {n} 筆（接收溢位）：匯流排比它能處理的還忙。",hint_socket_drops:"有 {n} 筆在 Home Assistant 讀取前就被丟掉了。",sparkline:"最近幾分鐘的負載","err_controller:rx_overflow":"接收溢位","err_controller:tx_overflow":"發送溢位","err_controller:rx_warning":"接收錯誤達警告","err_controller:tx_warning":"發送錯誤達警告","err_controller:rx_passive":"接收錯誤被動","err_controller:tx_passive":"發送錯誤被動","err_controller:active":"恢復正常",err_controller:"控制器問題","err_protocol:bit":"位元錯誤","err_protocol:form":"格式錯誤","err_protocol:stuff":"填充錯誤","err_protocol:bit0":"送不出顯性位元","err_protocol:bit1":"送不出隱性位元","err_protocol:overload":"匯流排過載","err_protocol:active_error":"主動錯誤旗標","err_protocol:on_tx":"發送時發生",err_protocol:"協定錯誤",err_tx_timeout:"發送逾時",err_lost_arbitration:"仲裁失敗",err_transceiver:"收發器問題",err_no_ack:"沒有人回 ACK",err_bus_off:"Bus off",err_bus_error:"匯流排錯誤",err_restarted:"控制器已重啟",source:"來源",file_source:"{name}（檔案）",pause:"暫停",resume:"繼續",clear:"清除",notch:"Notch",notch_clear:"清除 Notch",changing_only:"只看在變",hide_inactive:"隱藏 5 秒沒收到的",view_hex:"HEX",view_bin:"二進位",filter_ph:"篩選 ID：123, 7E0/7F0, 100-1FF",filter_bad:"看不懂：{x}",col_id:"ID",col_name:"名稱",col_len:"長度",col_data:"資料",col_count:"次數",col_hz:"Hz",col_period:"週期",col_dchg:"變化間隔",col_age:"距今",col_time:"時間",col_dir:"方向",dir_rx:"收",dir_tx:"送",dir_local:"本機",monitor_empty:"還沒收到任何訊框。請確認匯流排有接上、所有節點速率一致；或到「擷取」分頁開啟一個紀錄檔。",monitor_hint:"每個 ID 一列。數值變了會上色再慢慢淡掉：上升青、下降紅，一直在跳的（計數器、校驗碼）用灰紫。找訊號的方法：先不要操作 10 秒，按 Notch 兩三次直到畫面安靜，再操作設備，看哪幾格亮起來。",notch_added:"已遮掉 {n} 個最近 2 秒內變過的位元。",notch_none:"最近 2 秒沒有位元變動。",overflow:"ID 超過 4096 個，另外 {n} 筆只計數。",frames_total:"{ids} 個 ID · 共 {n} 筆",row_pin:"釘選",row_unpin:"取消釘選",row_send:"再送一次",row_events:"觸發事件",row_events_on:"已觸發事件",row_trace:"看時間序",row_notch:"遮掉這列",detail_period:"週期 {avg} ms（{min}–{max}）",detail_rate:"每秒 {hz} 筆",detail_changed:"資料最後變化：{ago}；最近兩次變化間隔 {gap}",paused_title:"已暫停：依時間排列（新的在前）",trace_older:"更早",trace_start:"已經是緩衝區裡最舊的一筆。",trace_all_dirs:"收送都看",trace_time:"時間",trace_delta:"間隔",trace_error:"錯誤訊框：{x}",trace_empty:"沒有符合的訊框。",events_added:"ID {id} 收到時，會觸發 woow_can_frame 事件。",gone:"介面重新載入了，正在重新連線…",offline_note:"紀錄檔 {file}：{n} 筆。監看顯示的是檔案結尾時的狀態。",send_title:"發送訊框",interface:"介面",frame:"訊框",frame_ph:"123#11223344",frame_help:"寫法：ID#資料。1–3 位數的 ID＝11-bit，更長＝29-bit；123#R＝遠端訊框；ID##1資料＝CAN FD（1＝切換速率）。",wait_id:"等回覆 ID",wait_ms:"等待（ms）",send:"送出",sent_ok:"已送出 {frame}",reply:"回覆 {frame}",no_reply:"沒有回覆（逾時）",cannot_send:"{name} 不能發送：{why}",why_listen:"設定為只監聽（到介面設定關閉）",why_unavailable:"目前無法使用",confirm_title:"第一次從 {name} 發送",confirm_text:"匯流排上的所有節點都會收到這筆訊框。如果是車輛、機器或電池的匯流排，請只送你清楚作用的訊框。",confirm_ok:"確定送出",periodic_title:"週期發送",periodic_hint:"每隔 N ms 送一次。Home Assistant 重新啟動後，所有項目都會先停止。",name:"名稱",period_ms:"週期（ms）",count:"次數（0＝不限）",running:"執行中",stopped:"已停止",sent_n:"已送 {n} 筆",stopped_by_count:"已送滿次數",stopped_by_error:"出錯停止：{x}",stopped_by_interface:"介面停止",periodic_empty:"還沒有週期發送。",capture_title:"錄製",capture_hint:"把介面的訊框錄成 candump 紀錄檔（canplayer、SavvyCAN、python-can、Wireshark 都能讀），存在 Home Assistant 設定資料夾的 woow_can/captures。下載和轉檔也可以選 Vector ASC、SavvyCAN CSV 或 pcap。",record:"開始錄製",stop_record:"停止",recording:"錄製中 · {n} 筆 · {size}",export:"下載緩衝區",export_hint:"記憶體裡最近的 {n} 筆，存成選定格式的檔案。",file_format:"格式",fmt_log:"candump log",fmt_asc:"Vector ASC",fmt_csv:"SavvyCAN CSV",fmt_pcap:"pcap（Wireshark）",fmt_trc:"PEAK TRC",fmt_crtd:"OVMS CRTD",convert:"轉檔",convert_hint:"把這個檔轉成 {fmt}，存在同一個資料夾",converted:"已寫出 {name}（{n} 筆）。",csv_note:"SavvyCAN CSV 只存傳統訊框（不含 CAN FD、遠端和錯誤訊框）。",files_title:"擷取檔",files_empty:"還沒有擷取檔。",download:"下載",open:"開啟",upload:"上傳紀錄檔",upload_hint:"candump log、Vector ASC、SavvyCAN CSV、PEAK TRC、OVMS CRTD 或 pcap",uploaded:"已上傳 {name}。",opened:"已開啟；到「監看」分頁把來源切到這個檔案。",offline_title:"已開啟的檔案",truncated:"只載入最後 {n} 筆",delete_confirm:"刪除 {name}？",all_channels:"全部來源",channel_service:"服務／AI",channel_panel:"面板",channel_entity:"實體",activity_hint:"AI（透過服務）和人（在這個面板）做的發送與變更，都記在這裡。",activity_empty:"還沒有紀錄。",quoted:"「{x}」",log_sent:"從 {port} 送出 {frame}",log_send_failed:"從 {port} 送出 {frame} 失敗：{error}",log_periodic_saved:"儲存週期發送「{name}」：{frame}，每 {period} ms，{port}",log_periodic_deleted:"刪除週期發送「{name}」",log_periodic_started:"開始週期發送「{name}」（{port}）",log_periodic_stopped:"停止週期發送「{name}」（已送 {sent} 筆）",log_periodic_failed:"週期發送「{name}」出錯停止：{error}",log_capture_started:"開始錄製 {file}（{port}）",log_capture_stopped:"停止錄製 {file}（{frames} 筆）",log_capture_deleted:"刪除擷取檔 {file}",log_capture_uploaded:"上傳擷取檔 {file}",log_capture_converted:"把 {file} 轉成 {target}（{frames} 筆）",log_monitor_cleared:"清除 {port} 的監看",tab_devices:"裝置",devices_hint:"裝置會把介面上選定的訊號變成 Home Assistant 實體。已知的設備從範本開始，也可以從匯入的 DBC 檔建立。",devices_empty:"還沒有裝置。從範本新增，或匯入 DBC 檔。",add_from_template:"從範本新增",import_dbc:"匯入 DBC",template:"範本",category_battery:"電池",category_vehicle:"車輛",category_marine:"船舶",category_industrial:"工業",confidence:"可信度：{x}",confidence_high:"高",confidence_medium:"中",confidence_low:"低",verified_with:"驗證依據：{x}",sources:"出處",license_x:"授權：{x}",only_listens:"只監聽，不會發送",groups_title:"訊息群組",groups_auto:"依實際流量判斷",groups_detect_hint:"會納入這個介面上已經收到過的群組。",device_name:"裝置名稱",create:"建立",created_device:"已建立 {name}。",messages_n:"{n} 則訊息",entities_n:"{n} 個實體",never_seen:"還沒收到",stale:"停止傳送",fresh:"持續收到",col_signal:"訊號",col_value:"數值",col_entity:"實體",adopt_hint:"勾選的訊號會成為 Home Assistant 實體。",state_on:"開",state_off:"關",entity_disabled:"停用中",settings:"設定",min_interval:"最短更新間隔（秒）",tolerance:"容差",timeout_s:"逾時（秒）",apply:"套用",delete_device_confirm:"刪除 {name} 和它的實體？",from_x:"來源：{x}",chart:"曲線",charts_title:"即時曲線",charts_empty:"在數值訊號旁按「曲線」，就會在這裡畫出來。",dbc_title:"DBC 檔",dbc_hint:"DBC 檔附加到介面後，監看會用它命名和解碼訊框；要變成實體，就從裡面挑訊息建立裝置。",dbc_empty:"還沒有 DBC 檔。",dbc_attached_to:"解碼介面",all_interfaces:"全部介面",dbc_warnings:"{n} 行看不懂",make_device:"建立裝置",download_dbc:"下載成 DBC",choose_messages:"訊息",imported_dbc:"已匯入 {name}：{m} 則訊息、{s} 個訊號。",decoded_title:"解碼",no_definition:"沒有裝置或 DBC 檔定義這個 ID。",log_device_created:"在 {port} 建立裝置「{device}」",log_device_updated:"修改裝置「{device}」（{port}）",log_device_from_template:"用範本 {template} 在 {port} 建立裝置「{device}」",log_device_from_dbc:"用 {file} 在 {port} 建立裝置「{device}」",log_device_deleted:"刪除裝置「{device}」",log_device_save_failed:"裝置「{device}」存不了：{error}",log_signal_changed:"{device}：修改訊號 {signal}",tab_analyze:"分析",an_source:"對象是 {name}（「監看」分頁選的來源）。",g_title:"引導式擷取：一個動作改變了什麼？",g_hint:"按「開始」，讓設備保持不動幾秒。按「下一步」後做動作（開門、按按鈕）並維持；再按「下一步」後還原。重複兩三次結果更準，最後按「完成」。",g_live_only:"引導式擷取要用即時的介面；請在「監看」分頁選一個介面。",g_start:"開始",g_next_action:"下一步：做動作",g_next_idle:"下一步：還原",g_finish:"完成",g_cancel:"取消",g_phase:"第 {n} 段：{label} · {s} 秒",g_do_idle:"讓設備保持不動。",g_do_action:"現在做動作並維持。",g_label_idle:"不動",g_label_action:"動作",g_results:"差異",g_none:"看不出明顯差異。每段多維持幾秒，或多重複幾次動作。",g_flip:"位元組 {byte} 第 {bit} 位：{a} → {b}",g_confirmed:"每次都一樣",g_shift:"位元組 {byte}：{a} → {b}",g_moving:"動作時變動：位元 {bits}",g_only:"只在動作時出現",g_counter:"計數器位元 {bits}",g_make_switch:"建立二元感測器",g_try_byte:"試解這個位元組",g_frames:"每段筆數：{n}",f_title:"依數值找訊號",f_hint:"從設備的螢幕讀一個數值（52.3 V、87%），輸入後開始。讓數值改變，輸入新數值再篩選；重複到只剩一兩個欄位。不知道數值時，可以不填就開始，之後依它怎麼變來篩。",f_value:"現在的數值",f_tolerance:"誤差",f_start:"用這個數值開始",f_start_blank:"不給數值開始",f_equals:"現在等於",f_increased:"變大",f_decreased:"變小",f_changed:"有變",f_unchanged:"沒變",f_clear:"清除",f_left:"剩 {n} 個候選，分布在 {ids} 個 ID",f_truncated:"只留最可能的",f_step_start:"開始",f_field:"位元 {start} 起 {length} 位",f_signed:"有號",f_open_bits:"位元檢視",f_add:"加入裝置",b_title:"單一 ID 的位元",b_hint:"顏色代表每個位元最近變動的頻率：深色＝每筆都變（計數器、檢查碼），淺色＝偶爾變，無色＝沒變。點一個位元當欄位起點，再點一個當終點。",b_id:"CAN ID",b_tx:"WOOW CAN 送出的",b_show:"顯示",b_frames:"{n} 筆",b_no_frames:"最近沒有這個 ID 的訊框。",b_byte:"位元組 {n}",b_little:"little endian（Intel）",b_big:"big endian（Motorola）",b_start:"起始位元",b_length:"長度",b_factor:"比例",b_offset:"偏移",b_unit:"單位",b_signed:"有號",b_try:"{n} 筆 · {d} 種值 · 變了 {c} 次 · {min} – {max} · 現在 {last}",b_bit_title:"第 {i} 位：變了 {c} 次（{p}%），{o}% 的訊框是 1",a_title:"把欄位加入裝置",a_name:"訊號名稱",a_device:"裝置",a_new_device:"新裝置",a_device_name:"新裝置名稱",a_interface:"介面",a_add:"加入",a_added:"已把 {signal} 加入 {device}。",a_name_needed:"請輸入訊號名稱。",row_analyze:"位元分析",log_signal_added:"{device}：加入訊號 {signal}",log_dbc_imported:"匯入 {file}（{messages} 則訊息）",log_dbc_attached:"{file} 解碼 {ports}",log_dbc_deleted:"刪除 {file}"};function It(t){const e=t.toLowerCase().startsWith("zh")?Dt:Et;return(t,i)=>{let s=e[t]??Et[t]??t;if(i)for(const[t,e]of Object.entries(i))s=s.split(`{${t}}`).join(String(e));return s}}function Nt(t){return t in Et}function Mt(t,e,i=Date.now()/1e3){const s=Math.max(0,i-t);return s<5?e("just_now"):s<60?e("s_ago",{n:Math.floor(s)}):s<3600?e("m_ago",{n:Math.floor(s/60)}):s<86400?e("h_ago",{n:Math.floor(s/3600)}):e("d_ago",{n:Math.floor(s/86400)})}function Tt(t){const e=new Date(1e3*t),i=(t,e=2)=>String(t).padStart(e,"0");return`${i(e.getHours())}:${i(e.getMinutes())}:${i(e.getSeconds())}.${i(e.getMilliseconds(),3)}`}function zt(t){return null!=t&&isFinite(t)?t<1?`${(1e3*t).toFixed(t<.01?2:1)} ms`:t<100?`${t.toFixed(2)} s`:`${Math.round(t)} s`:"–"}function Ot(t){return t<1024?`${t} B`:t<1048576?`${(t/1024).toFixed(1)} KB`:`${(t/1024/1024).toFixed(1)} MB`}function Pt(t){return null==t?"–":`${t.toFixed(t<10?1:0)}%`}const Rt=o`
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
`,Ft=o`
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
`;class Bt extends lt{constructor(){super(...arguments),this.entries=[],this.now=0,this.channel=""}channelLabel(t){const e=`channel_${t}`;return Nt(e)?this.t(e):t}message(t){const e=`log_${t.msg}`;return t.msg&&Nt(e)?this.t(e,{...t.args??{}}):t.summary}render(){const t=this.t,e=this.entries.filter(t=>!this.channel||t.channel===this.channel).sort((t,e)=>e.t-t.t);return L`<div class="card">
      <div class="row">
        <h2 class="grow">${t("tab_activity")}</h2>
        <select @change=${t=>this.channel=(t=>t.target.value)(t)}>
          <option value="">${t("all_channels")}</option>
          ${["service","panel","entity"].map(t=>L`<option value=${t}>${this.channelLabel(t)}</option>`)}
        </select>
      </div>
      <div class="muted">${t("activity_hint")}</div>
      ${0===e.length?L`<div class="empty">${t("activity_empty")}</div>`:e.map(e=>L`<div class="entry">
              <div class="when" title=${new Date(1e3*e.t).toLocaleString()}>${Mt(e.t,t)}<br />${Tt(e.t).slice(0,8)}</div>
              <div>
                <div class="row">
                  <span class="chip ${"service"===e.channel?"info":""}">${this.channelLabel(e.channel)}</span>
                  ${e.user?L`<span class="chip">${e.user}</span>`:K}
                  ${e.port_id?L`<span class="muted">${this.portName(e.port_id)}</span>`:K}
                </div>
                <div class=${e.ok?"":"fail"} title=${e.summary}>${e.ok?"":"✗ "}${this.message(e)}</div>
                ${e.note?L`<div class="note">${t("quoted",{x:e.note})}</div>`:K}
              </div>
            </div>`)}
    </div>`}}Bt.styles=[Rt,o`
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
    `],t([ut({attribute:!1})],Bt.prototype,"entries",void 0),t([ut({attribute:!1})],Bt.prototype,"now",void 0),t([ut({attribute:!1})],Bt.prototype,"t",void 0),t([ut({attribute:!1})],Bt.prototype,"portName",void 0),t([mt()],Bt.prototype,"channel",void 0),St("woow-can-activity",Bt);const Ut=t=>t.target.value,Ht=t=>t.target.checked;function jt(t,e=""){if(null==t)return"–";if("boolean"==typeof t)return t?"on":"off";if("number"==typeof t){const i=Number.isInteger(t)?String(t):String(parseFloat(t.toFixed(3)));return e?`${i} ${e.replace("degC","°C").replace("degF","°F")}`:i}return String(t)}class Wt extends lt{constructor(){super(...arguments),this.interfaces=[],this.devices=[],this.values={},this.history={},this.charts=[],this.templates=[],this.databases=[],this.preferredInterface="",this.open="",this.draft=null,this.busy=!1,this.message=null,this.deleting="",this.settingsFor="",this.settings={min_interval:"",tolerance:"",timeout:""},this.dbcDevice=null,this.iname=t=>this.interfaces.find(e=>e.id===t)?.name??"?"}async run(t,e){this.busy=!0;try{return await t(),this.message=e?{ok:!0,text:e}:null,!0}catch(t){return this.message={ok:!1,text:this.t("error",{msg:kt(t)})},!1}finally{this.busy=!1}}moreInfo(t){this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:t},bubbles:!0,composed:!0}))}toggleChart(t){this.dispatchEvent(new CustomEvent("toggle-chart",{detail:t}))}startTemplate(){const t=this.templates[0],e=this.interfaces.find(t=>t.id===this.preferredInterface)??this.interfaces[0];this.draft=t?this.draftFor(t,e?.id??""):null,this.message=null}draftFor(t,e){return{template:t.id,entryId:e,name:"",params:Object.fromEntries(t.params.map(t=>[t.key,null===t.default||void 0===t.default?"":String(t.default)])),auto:!0,groups:[]}}async createFromTemplate(){const t=this.draft;if(!t)return;const e=this.templates.find(e=>e.id===t.template),i={};for(const s of e?.params??[]){const e=t.params[s.key]??"";i[s.key]="number"!=typeof s.default||""===e||isNaN(Number(e))?e:Number(e)}let s=null;await this.run(async()=>{s=await this.api.createFromTemplate(t.template,t.entryId,t.name,i,t.auto?null:t.groups)})&&s&&(this.draft=null,this.open=s.id,this.message={ok:!0,text:this.t("created_device",{name:s.name})})}renderTemplateDialog(){const t=this.draft;if(!t)return K;const e=this.t,i=this.templates.find(e=>e.id===t.template),s=e=>this.draft={...t,...e},a=(t,i)=>Nt(`${t}_${i}`)?e(`${t}_${i}`):i;return L`<div class="scrim" @click=${t=>t.target===t.currentTarget&&(this.draft=null)}>
      <div class="dialog">
        <div>
          ${this.templates.map(e=>L`<button class="tpl ${e.id===t.template?"on":""}"
            @click=${()=>this.draft=this.draftFor(e,t.entryId)}>
            <div><b>${e.name}</b></div>
            <div class="muted">${a("category",e.category)} · ${a("confidence",e.confidence)}</div>
          </button>`)}
        </div>
        ${i?L`<div class="form">
              <h2 style="margin:0;font-size:1.15em;font-weight:500">${i.name}</h2>
              <div>${i.description}</div>
              ${i.notes?L`<div class="muted">${i.notes}</div>`:K}
              <div class="row">
                <span class="chip ok">${e("only_listens")}</span>
                <span class="chip">${e("confidence",{x:a("confidence",i.confidence)})}</span>
                ${i.bitrate?L`<span class="chip">${e("kbps",{n:i.bitrate/1e3})}</span>`:K}
              </div>
              <div class="muted">${e("verified_with",{x:i.verified.join("；")})}</div>
              <details>
                <summary>${e("sources")}</summary>
                <ul>${i.source.map(t=>L`<li>${t}</li>`)}</ul>
                <div class="muted">${e("license_x",{x:i.license})}</div>
              </details>
              <label class="field">${e("interface")}
                <select @change=${t=>s({entryId:Ut(t)})}>
                  ${this.interfaces.map(e=>L`<option value=${e.id} ?selected=${e.id===t.entryId}>${e.name} · ${e.port}</option>`)}
                </select>
              </label>
              <label class="field">${e("device_name")}
                <input .value=${t.name} placeholder=${i.default_name} @input=${t=>s({name:Ut(t)})} />
              </label>
              ${i.params.map(e=>L`<label class="field">${e.key} — ${e.description}
                <input .value=${t.params[e.key]??""} @input=${i=>s({params:{...t.params,[e.key]:Ut(i)}})} />
              </label>`)}
              ${i.groups.length?L`<div>
                    <div class="muted">${e("groups_title")}</div>
                    <label class="row"><input type="checkbox" .checked=${t.auto}
                      @change=${t=>s({auto:Ht(t)})} />${e("groups_auto")}</label>
                    ${t.auto?L`<div class="muted">${e("groups_detect_hint")}</div>`:i.groups.map(e=>L`<label class="row"><input type="checkbox" .checked=${t.groups.includes(e.id)}
                          @change=${i=>s({groups:Ht(i)?[...t.groups,e.id]:t.groups.filter(t=>t!==e.id)})} />
                          ${e.name}</label>`)}
                  </div>`:K}
              ${this.message&&!this.message.ok?L`<div class="chip bad" style="white-space:normal">${this.message.text}</div>`:K}
              <div class="row">
                <span class="grow"></span>
                <button @click=${()=>this.draft=null}>${e("cancel")}</button>
                <button class="primary" ?disabled=${this.busy||!t.entryId} @click=${()=>this.createFromTemplate()}>${e("create")}</button>
              </div>
            </div>`:K}
      </div>
    </div>`}async adopt(t,e,i,s){await this.run(()=>this.api.setSignal(t.id,e,i.name,{adopted:s}))}openSettings(t,e,i){const s=`${t.id}|${e}.${i}`;if(this.settingsFor===s)return void(this.settingsFor="");const a=t.definition?.messages.find(t=>t.name===e)?.signals.find(t=>t.name===i),r=a?.entity??{};this.settings={min_interval:void 0!==r.min_interval?String(r.min_interval):"",tolerance:void 0!==r.tolerance?String(r.tolerance):"",timeout:void 0!==r.timeout?String(r.timeout):""},this.settingsFor=s}async applySettings(t,e,i){const s={};for(const t of["min_interval","tolerance","timeout"]){const e=this.settings[t].trim();s[t]=""===e?null:Number(e)}await this.run(()=>this.api.setSignal(t.id,e,i,{entity:s}))&&(this.settingsFor="")}renderDevice(t){const e=this.t,i=this.values[t.id]??{},s=t.status,a=s.reduce((t,e)=>t+e.signals.filter(t=>t.adopted).length,0),r=s.filter(t=>!0===t.fresh).length,o=s.filter(t=>!1===t.fresh&&null!==t.seen_s_ago).length,n=s.filter(t=>null===t.seen_s_ago).length,c=this.open===t.id;return L`<div class="device">
      <div class="row">
        <h3>${t.name}</h3>
        <span class="chip">${this.iname(t.interface)}</span>
        ${t.template?L`<span class="chip info">${this.templates.find(e=>e.id===t.template)?.name??t.template}</span>`:K}
        ${t.source.startsWith("dbc:")?L`<span class="chip info">${t.source.slice(4)}</span>`:K}
        <span class="grow"></span>
        <button class="link" @click=${()=>this.open=c?"":t.id}>${c?"▲":"▼"}</button>
      </div>
      <div class="muted">
        ${e("messages_n",{n:s.length})} · ${e("entities_n",{n:a})}
        ${r?L` · <span class="rx">${r} ${e("fresh")}</span>`:K}
        ${o?L` · <span style="color:var(--warning-color)">${o} ${e("stale")}</span>`:K}
        ${n?L` · ${n} ${e("never_seen")}`:K}
      </div>
      ${c?L`${s.map(s=>L`<div class="msg">
              <div class="row">
                <b>${s.name}</b><span class="muted mono">${s.id}</span>
                <span class="chip ${!0===s.fresh?"ok":!1===s.fresh&&null!==s.seen_s_ago?"warn":""}">
                  ${null===s.seen_s_ago?e("never_seen"):!1===s.fresh?e("stale"):e("fresh")}</span>
              </div>
              <div class="wrap"><table>
                <colgroup><col class="c-adopt" /><col class="c-name" /><col class="c-value" /><col /><col class="c-actions" /></colgroup>
                <tbody>
                  ${s.signals.map(a=>{const r=`${s.name}.${a.name}`,o=r in i?i[r]:a.value,n=`${t.id}|${r}`,c="number"==typeof o&&"binary_sensor"!==a.platform;return L`<tr>
                        <td><input type="checkbox" title=${e("adopt_hint")} .checked=${a.adopted}
                          @change=${e=>this.adopt(t,s.name,a,Ht(e))} /></td>
                        <td>${a.name}</td>
                        <td class="val">${"binary_sensor"!==a.platform||0!==o&&1!==o&&"boolean"!=typeof o?jt(o,a.unit):e(1===o||!0===o?"state_on":"state_off")}</td>
                        <td title=${a.entity_id??""}>${a.entity_id?a.disabled?L`<span class="off-entity">${a.entity_id} · ${e("entity_disabled")}</span>`:L`<a class="entity" @click=${()=>this.moreInfo(a.entity_id)}>${a.entity_id}</a>`:K}</td>
                        <td class="row">
                          ${c||this.charts.includes(n)?L`<button class="link" @click=${()=>this.toggleChart(n)}>
                                ${this.charts.includes(n)?"✓ ":""}${e("chart")}</button>`:K}
                          ${a.adopted?L`<button class="link" @click=${()=>this.openSettings(t,s.name,a.name)}>${e("settings")}</button>`:K}
                        </td>
                      </tr>
                      ${this.settingsFor===n?L`<tr><td colspan="5"><div class="inline">
                            ${["min_interval","tolerance","timeout"].map(t=>L`<label class="field">
                              ${e("timeout"===t?"timeout_s":t)}
                              <input type="number" step="any" .value=${this.settings[t]}
                                @input=${e=>this.settings={...this.settings,[t]:Ut(e)}} /></label>`)}
                            <button class="primary" @click=${()=>this.applySettings(t,s.name,a.name)}>${e("apply")}</button>
                          </div></td></tr>`:K}`})}
                </tbody>
              </table></div>
            </div>`)}
            <div class="row">
              <button class="link" @click=${()=>this.run(()=>this.api.download(`/api/woow_can/devices/${t.id}/dbc`))}>
                ${e("download_dbc")}</button>
              <span class="grow"></span>
              ${this.deleting===t.id?L`<span>${e("delete_device_confirm",{name:t.name})}</span>
                    <button class="danger" @click=${()=>this.run(async()=>{this.deleting="",await this.api.deleteDevice(t.id)})}>${e("delete")}</button>
                    <button @click=${()=>this.deleting=""}>${e("cancel")}</button>`:L`<button class="link danger" @click=${()=>this.deleting=t.id}>${e("delete")}</button>`}
            </div>`:K}
    </div>`}renderCharts(){const t=this.t;return this.charts.length?L`<div class="card">
      <div class="row"><h2 class="grow">${t("charts_title")}</h2></div>
      <div class="charts">
        ${this.charts.map(t=>{const[e,i]=t.split("|"),s=this.devices.find(t=>t.id===e),a=this.history[t]??[];let r="";for(const t of s?.status??[])for(const e of t.signals)`${t.name}.${e.name}`===i&&(r=e.unit);const o=this.values[e]?.[i],n=a.map(t=>t[1]),c=n.length?Math.min(...n):0,l=n.length?Math.max(...n):1,d=l-c||1,h=a.length?a[0][0]:0,p=(a.length?a[a.length-1][0]:1)-h||1,u=a.map(([t,e])=>`${((t-h)/p*300).toFixed(1)},${(56-(e-c)/d*52).toFixed(1)}`);return L`<div class="chart">
            <div class="row"><span class="muted grow">${s?.name??"?"} · ${i}</span>
              <button class="link" @click=${()=>this.toggleChart(t)}>✕</button></div>
            <b>${jt(o,r)}</b>
            <svg class="line" viewBox="0 0 300 60" preserveAspectRatio="none">
              ${V`<line x1="0" y1="58" x2="300" y2="58"></line>`}
              ${u.length>1?V`<polyline points=${u.join(" ")}></polyline>`:K}
            </svg>
            <div class="muted">${n.length?`${jt(c)} – ${jt(l)}`:""}</div>
          </div>`})}
      </div>
    </div>`:K}async upload(t){const e=t.target,i=e.files?.[0];if(e.value="",!i)return;const s=this.preferredInterface&&this.interfaces.some(t=>t.id===this.preferredInterface)?[this.preferredInterface]:[];await this.run(async()=>{const t=await this.api.uploadDbc(i,s);this.message={ok:!0,text:this.t("imported_dbc",{name:t.name,m:t.messages,s:t.signals})}})}async setAttach(t,e,i){const s=i?[...t.attached.filter(t=>t!==e),e]:t.attached.filter(t=>t!==e);await this.run(()=>this.api.dbc("attach",t.name,{interfaces:s}))}async createFromDbc(){const t=this.dbcDevice;if(!t)return;await this.run(()=>this.api.dbc("create_device",t.name,{entry_id:t.entryId,device_name:t.deviceName,messages:t.messages.length?t.messages:void 0}))&&(this.dbcDevice=null)}renderDatabases(){const t=this.t;return L`<div class="card">
      <div class="row">
        <h2 class="grow">${t("dbc_title")}</h2>
        <button @click=${()=>this.renderRoot.querySelector("#dbc")?.click()}>${t("import_dbc")}</button>
        <input id="dbc" type="file" accept=".dbc" @change=${this.upload} />
      </div>
      <div class="muted">${t("dbc_hint")}</div>
      ${0===this.databases.length?L`<div class="empty">${t("dbc_empty")}</div>`:this.databases.map(e=>L`<div class="device" style="margin-top:10px">
            <div class="row">
              <b class="mono">${e.name}</b>
              <span class="muted">${t("messages_n",{n:e.messages})} · ${e.signals}</span>
              ${e.warning_count?L`<details><summary>${t("dbc_warnings",{n:e.warning_count})}</summary>
                <ul>${e.warnings.map(t=>L`<li class="mono">${t}</li>`)}</ul></details>`:K}
              <span class="grow"></span>
              <button class="link" @click=${()=>this.api.download(`/api/woow_can/dbc/${encodeURIComponent(e.name)}`)}>${t("download")}</button>
              <button class="link" @click=${()=>this.dbcDevice={name:e.name,entryId:this.preferredInterface||this.interfaces[0]?.id||"",deviceName:"",messages:[]}}>${t("make_device")}</button>
              <button class="link danger" @click=${()=>this.run(()=>this.api.dbc("delete",e.name))}>${t("delete")}</button>
            </div>
            <div class="row">
              <span class="muted">${t("dbc_attached_to")}:</span>
              <label class="row"><input type="checkbox" .checked=${e.attached.includes("*")}
                @change=${t=>this.setAttach(e,"*",Ht(t))} />${t("all_interfaces")}</label>
              ${this.interfaces.map(t=>L`<label class="row"><input type="checkbox" .checked=${e.attached.includes(t.id)}
                @change=${i=>this.setAttach(e,t.id,Ht(i))} />${t.name}</label>`)}
            </div>
            ${this.dbcDevice?.name===e.name?L`<div class="inline">
                  <label class="field">${t("interface")}
                    <select @change=${t=>this.dbcDevice={...this.dbcDevice,entryId:Ut(t)}}>
                      ${this.interfaces.map(t=>L`<option value=${t.id} ?selected=${t.id===this.dbcDevice.entryId}>${t.name}</option>`)}
                    </select></label>
                  <label class="field">${t("device_name")}<input .value=${this.dbcDevice.deviceName} placeholder=${e.name.replace(/\.dbc$/i,"")}
                    @input=${t=>this.dbcDevice={...this.dbcDevice,deviceName:Ut(t)}} /></label>
                  <div>
                    <div class="muted">${t("choose_messages")}</div>
                    ${e.message_names.map(t=>L`<label class="row"><input type="checkbox" .checked=${this.dbcDevice.messages.includes(t)}
                      @change=${e=>this.dbcDevice={...this.dbcDevice,messages:Ht(e)?[...this.dbcDevice.messages,t]:this.dbcDevice.messages.filter(e=>e!==t)}} />
                      <span class="mono">${t}</span></label>`)}
                  </div>
                  <button class="primary" ?disabled=${this.busy} @click=${()=>this.createFromDbc()}>${t("create")}</button>
                  <button @click=${()=>this.dbcDevice=null}>${t("cancel")}</button>
                </div>`:K}
          </div>`)}
    </div>`}render(){const t=this.t;return L`<div class="card">
        <div class="row">
          <h2 class="grow">${t("tab_devices")}</h2>
          <button class="primary" ?disabled=${!this.templates.length||!this.interfaces.length} @click=${()=>this.startTemplate()}>
            ${t("add_from_template")}</button>
        </div>
        <div class="muted">${t("devices_hint")}</div>
        ${this.message&&!this.draft?L`<div class="chip ${this.message.ok?"ok":"bad"}" style="margin-top:8px;white-space:normal">${this.message.text}</div>`:K}
        ${0===this.devices.length?L`<div class="empty">${t("devices_empty")}</div>`:L`<div class="devices" style="margin-top:12px">${this.devices.map(t=>this.renderDevice(t))}</div>`}
      </div>
      ${this.renderCharts()} ${this.renderDatabases()} ${this.renderTemplateDialog()}`}}Wt.styles=[Rt,o`
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
    `],t([ut({attribute:!1})],Wt.prototype,"interfaces",void 0),t([ut({attribute:!1})],Wt.prototype,"devices",void 0),t([ut({attribute:!1})],Wt.prototype,"values",void 0),t([ut({attribute:!1})],Wt.prototype,"history",void 0),t([ut({attribute:!1})],Wt.prototype,"charts",void 0),t([ut({attribute:!1})],Wt.prototype,"templates",void 0),t([ut({attribute:!1})],Wt.prototype,"databases",void 0),t([ut({attribute:!1})],Wt.prototype,"preferredInterface",void 0),t([ut({attribute:!1})],Wt.prototype,"t",void 0),t([ut({attribute:!1})],Wt.prototype,"api",void 0),t([mt()],Wt.prototype,"open",void 0),t([mt()],Wt.prototype,"draft",void 0),t([mt()],Wt.prototype,"busy",void 0),t([mt()],Wt.prototype,"message",void 0),t([mt()],Wt.prototype,"deleting",void 0),t([mt()],Wt.prototype,"settingsFor",void 0),t([mt()],Wt.prototype,"settings",void 0),t([mt()],Wt.prototype,"dbcDevice",void 0),St("woow-can-devices",Wt);const Lt=t=>t.target.value,Vt=t=>bt(t%vt)+(t>=vt?" (tx)":"");class qt extends lt{constructor(){super(...arguments),this.interfaces=[],this.offline=[],this.devices=[],this.source="",this.focusId=null,this.message=null,this.busy=!1,this.guided=null,this.tick=0,this.find=null,this.findValue="",this.findTol="",this.idText="",this.tx=!1,this.bits=null,this.spec={start:0,length:8,byte_order:"little",signed:!1,factor:1,offset:0},this.ends=null,this.anchor=null,this.trial=null,this.add=null,this.lastFocus=0}connectedCallback(){super.connectedCallback(),this.timer=window.setInterval(()=>{this.guided?.running&&this.tick++},250),this.refresh()}disconnectedCallback(){super.disconnectedCallback(),window.clearInterval(this.timer),window.clearTimeout(this.trialTimer)}willUpdate(t){t.has("source")&&void 0!==t.get("source")&&(this.guided=null,this.find=null,this.bits=null,this.trial=null,this.refresh()),t.has("focusId")&&this.focusId&&this.focusId.n!==this.lastFocus&&(this.lastFocus=this.focusId.n,this.idText=bt(this.focusId.key%vt),this.tx=this.focusId.key>=vt,this.loadBits())}get live(){return this.interfaces.some(t=>t.id===this.source)}get sourceName(){const t=this.interfaces.find(t=>t.id===this.source);return t?`${t.name} · ${t.port}`:this.offline.find(t=>t.id===this.source)?.name??"?"}async refresh(){if(this.source)try{if(this.find=await this.api.analyzeFind(this.source,"status"),0===this.find.steps.length&&(this.find=null),this.live){const t=await this.api.analyzeGuided(this.source,"status");this.guided=t.phases.length?t:null}}catch{}}async run(t){this.busy=!0,this.message=null;try{await t()}catch(t){this.message={ok:!1,text:this.t("error",{msg:kt(t)})}}finally{this.busy=!1}}guidedStep(t){return this.run(async()=>{const e=this.guided?.phases.length??0,i="start"===t?this.t("g_label_idle"):"next"===t?this.t(e%2?"g_label_action":"g_label_idle"):void 0,s=await this.api.analyzeGuided(this.source,t,i);this.guided="cancel"===t?null:s})}renderGuided(){const t=this.t,e=this.guided,i=!!e?.running,s=e?.phases??[],a=i?s[s.length-1]:null;this.tick;const r=a?Math.max(0,Date.now()/1e3-a.start):0,o=s.length%2==0;return L`<div class="card">
      <h2>${t("g_title")}</h2>
      <div class="muted">${t("g_hint")}</div>
      ${this.live?i?L`<div class="phase">${t("g_phase",{n:s.length,label:a.label,s:r.toFixed(1)})}</div>
              <div>${t(o?"g_do_action":"g_do_idle")}</div>
              <div class="steps">
                <button class="primary" ?disabled=${this.busy||s.length>=9} @click=${()=>this.guidedStep("next")}>
                  ${t(o?"g_next_idle":"g_next_action")}</button>
                <button ?disabled=${this.busy||s.length<2} @click=${()=>this.guidedStep("finish")}>${t("g_finish")}</button>
                <button class="link" ?disabled=${this.busy} @click=${()=>this.guidedStep("cancel")}>${t("g_cancel")}</button>
              </div>`:L`<div class="steps">
              <button class="primary" ?disabled=${this.busy} @click=${()=>this.guidedStep("start")}>${t("g_start")}</button>
            </div>`:L`<div class="chip warn" style="margin-top:8px">${t("g_live_only")}</div>`}
      ${e&&!i&&e.results?this.renderGuidedResults(e):K}
    </div>`}renderGuidedResults(t){const e=this.t,i=t.results??[];return L`<h2 style="margin-top:12px">${e("g_results")}</h2>
      <div class="muted">${t.phases.map(t=>`${t.label} ${t.seconds} s`).join(" → ")}
        ${t.frames?L` · ${e("g_frames",{n:t.frames.join(" / ")})}`:K}</div>
      ${t.warning?L`<div class="chip warn" style="white-space:normal">${t.warning}</div>`:K}
      ${0===i.length?L`<div class="empty">${e("g_none")}</div>`:i.map(t=>this.renderGuidedRow(t))}`}renderGuidedRow(t){const e=this.t,i=t=>t[0]===t[1]?`${t[0]}`:`${t[0]}–${t[1]}`;return L`<div class="result">
      <div class="row"><b class="mono">${t.id}</b>
        <button class="link" @click=${()=>this.openBits(t.key)}>${e("f_open_bits")}</button></div>
      ${t.only_in?L`<div class="hint-row"><span class="chip info">${e("g_only")}</span></div>`:K}
      ${(t.flipped??[]).map(i=>L`<div class="hint-row">
        <span class="chip ok">${e("g_flip",{byte:i.byte,bit:i.bit,a:i.idle,b:i.action})}</span>
        ${i.confirmed?L`<span class="muted">✓ ${e("g_confirmed")}</span>`:K}
        <button class="link" @click=${()=>this.openAdd(t.key,{start:i.start,length:1,byte_order:"little",signed:!1,factor:1,offset:0})}>
          ${e("g_make_switch")}</button>
      </div>`)}
      ${(t.shifted_bytes??[]).map(s=>L`<div class="hint-row">
        <span class="chip info">${e("g_shift",{byte:s.byte,a:i(s.idle),b:i(s.action)})}</span>
        ${s.confirmed?L`<span class="muted">✓ ${e("g_confirmed")}</span>`:K}
        <button class="link" @click=${()=>this.openBits(t.key,{start:8*s.byte,length:8,byte_order:"little",signed:!1,factor:1,offset:0})}>
          ${e("g_try_byte")}</button>
      </div>`)}
      ${t.moving?.length?L`<div class="muted">${e("g_moving",{bits:t.moving.map(t=>t.start).join(", ")})}</div>`:K}
      ${t.counter_bits?.length?L`<div class="muted">${e("g_counter",{bits:this.spans(t.counter_bits)})}</div>`:K}
    </div>`}spans(t){const e=[];let i=t[0],s=t[0];for(const a of t.slice(1).concat([NaN]))a!==s+1?(e.push(i===s?`${i}`:`${i}–${s}`),i=s=a):s=a;return e.join(", ")}parse(t){const e=parseFloat(t.replace(",","."));return Number.isFinite(e)?e:null}findStep(t,e,i=!0){return this.run(async()=>{const s=i?this.parse(this.findValue):null,a=this.parse(this.findTol),r=await this.api.analyzeFind(this.source,t,{mode:e,value:s,tolerance:a});this.find="clear"===t?null:r})}renderFind(){const t=this.t,e=this.find,i=this.parse(this.findValue);return L`<div class="card">
      <h2>${t("f_title")}</h2>
      <div class="muted">${t("f_hint")}</div>
      <div class="form">
        <label>${t("f_value")}<input type="number" step="any" .value=${this.findValue}
          @input=${t=>this.findValue=Lt(t)} /></label>
        <label>${t("f_tolerance")}<input type="number" step="any" min="0" .value=${this.findTol} placeholder="auto"
          @input=${t=>this.findTol=Lt(t)} /></label>
        ${e?L`<button class="primary" ?disabled=${this.busy||null===i} @click=${()=>this.findStep("narrow","equals")}>
                ${t("f_equals")}</button>
              ${["increased","decreased","changed","unchanged"].map(e=>L`<button ?disabled=${this.busy}
                @click=${()=>this.findStep("narrow",e,!1)}>${t(`f_${e}`)}</button>`)}
              <button class="link" ?disabled=${this.busy} @click=${()=>this.findStep("clear")}>${t("f_clear")}</button>`:L`<button class="primary" ?disabled=${this.busy||null===i} @click=${()=>this.findStep("start")}>${t("f_start")}</button>
              <button ?disabled=${this.busy} @click=${()=>this.findStep("start",void 0,!1)}>${t("f_start_blank")}</button>`}
      </div>
      ${e?this.renderCandidates(e):K}
    </div>`}modeName(t){const e=`f_${t}`;return Nt(e)?this.t(e):t}renderCandidates(t){const e=this.t;return L`<div><b>${e("f_left",{n:t.left.toLocaleString(),ids:t.ids})}</b>
        ${t.truncated?L`<span class="muted">· ${e("f_truncated")}</span>`:K}</div>
      <div class="muted">${t.steps.map(t=>`${"start"===t.mode?e("f_step_start"):"equals"===t.mode?`= ${t.value}`:this.modeName(t.mode)} → ${t.left}`).join(" · ")}</div>
      ${t.candidates.map(t=>L`<div class="cand">
        <b class="mono">${t.id}</b>
        <span>${e("f_field",{start:t.start,length:t.length})} · ${"big"===t.byte_order?"BE":"LE"}${t.signed?` · ${e("f_signed")}`:""}</span>
        <span class="muted">${(t=>{const e=[];return 1!==t.factor&&e.push(`× ${t.factor}`),t.offset&&e.push(`${t.offset>0?"+":"−"} ${Math.abs(t.offset)}`),e.join(" ")||"—"})(t)}</span>
        <b class="val">${jt(t.value)}</b>
        <span class="grow"></span>
        <button class="link" @click=${()=>this.openBits(t.key,t)}>${e("f_open_bits")}</button>
        <button class="link" @click=${()=>this.openAdd(t.key,t)}>${e("f_add")}</button>
      </div>`)}`}currentKey(){try{const[t,e]=wt(this.idText);return(e?t+2147483648:t)+(this.tx?vt:0)}catch{return null}}openBits(t,e){this.idText=bt(t%vt),this.tx=t>=vt,e&&(this.spec={start:e.start,length:e.length,byte_order:e.byte_order,signed:e.signed,factor:e.factor,offset:e.offset},this.ends=null,this.anchor=null),this.loadBits().then(()=>this.renderRoot.querySelector("#bits")?.scrollIntoView({behavior:"smooth"}))}async loadBits(){const t=this.currentKey();null!==t&&(await this.run(async()=>{this.bits=await this.api.analyzeBits(this.source,t,60)}),this.scheduleTrial(0))}scheduleTrial(t=300){window.clearTimeout(this.trialTimer),this.trialTimer=window.setTimeout(()=>{this.tryField()},t)}async tryField(){const t=this.currentKey();if(null!==t&&this.bits?.frames)try{this.trial=await this.api.analyzeTry(this.source,t,this.spec,60)}catch(t){this.trial=null,this.message={ok:!1,text:this.t("error",{msg:kt(t)})}}}setSpec(t){this.spec={...this.spec,...t},"byte_order"in t&&this.ends&&(this.spec={...this.spec,..._t(this.ends[0],this.ends[1],this.spec.byte_order)}),this.scheduleTrial()}tapBit(t){null===this.anchor?(this.anchor=t,this.ends=[t,t],this.spec={...this.spec,start:t,length:1}):(this.ends=[this.anchor,t],this.spec={...this.spec,..._t(this.anchor,t,this.spec.byte_order)},this.anchor=null),this.scheduleTrial()}renderBits(){const t=this.t,e=this.bits,i=this.currentKey();return L`<div class="card" id="bits">
      <h2>${t("b_title")}</h2>
      <div class="muted">${t("b_hint")}</div>
      <div class="form">
        <label>${t("b_id")}<input class="mono" style="width:110px" .value=${this.idText}
          @input=${t=>this.idText=Lt(t).trim()} @change=${()=>this.loadBits()} /></label>
        <label class="toggle" style="flex-direction:row;align-items:center"><input type="checkbox" .checked=${this.tx}
          @change=${t=>{this.tx=t.target.checked,this.loadBits()}} />${t("b_tx")}</label>
        <button ?disabled=${this.busy||null===i} @click=${()=>this.loadBits()}>${t("b_show")}</button>
        ${e?L`<span class="muted">${t("b_frames",{n:e.frames})}</span>`:K}
      </div>
      ${e&&0===e.frames?L`<div class="empty">${t("b_no_frames")}</div>`:K}
      ${e&&e.frames?this.renderGrid(e):K}
      ${e&&e.frames?this.renderField():K}
    </div>`}renderGrid(t){const e=this.t,i=new Set(function(t,e,i){if("little"===i)return Array.from({length:e},(e,i)=>t+i);const s=8*Math.floor(t/8)+(7-t%8);return Array.from({length:e},(t,e)=>{const i=s+e;return 8*Math.floor(i/8)+(7-i%8)})}(this.spec.start,this.spec.length,this.spec.byte_order)),s=Math.max(1,t.frames-1),a=[];for(let r=0;r<t.length;r++){a.push(L`<span class="lbl">${e("b_byte",{n:r})}</span>`);for(let o=7;o>=0;o--){const n=8*r+o,c=t.changes[n]/s,l=t.ones[n]/t.frames,d=t.changes[n]?Math.round(15+70*Math.min(1,c)):0,h=d?`background: color-mix(in srgb, #00bbff ${d}%, transparent)`:"",p=e("b_bit_title",{i:n,c:t.changes[n],p:Math.round(100*c),o:Math.round(100*l)});a.push(L`<span class="cell ${i.has(n)?"sel":""} ${this.anchor===n?"anchor":""}" style=${h}
          title=${p} @click=${()=>this.tapBit(n)}>${l>=.5?"1":"0"}</span>`)}const o=t.bytes[r];a.push(L`<span class="lbl mono">${o.min===o.max?o.min.toString(16).toUpperCase().padStart(2,"0"):`${o.min.toString(16).toUpperCase().padStart(2,"0")}–${o.max.toString(16).toUpperCase().padStart(2,"0")}`}</span>`)}return L`<div class="wrap"><div class="grid">
      <span></span>${[7,6,5,4,3,2,1,0].map(t=>L`<span class="lbl" style="text-align:center">${t}</span>`)}<span></span>
      ${a}
    </div></div>`}renderField(){const t=this.t,e=this.spec,i=this.trial,s=(i?.samples??[]).filter(t=>"number"==typeof t.value);let a=K;if(s.length>1){const t=s.map(t=>t.value),e=Math.min(...t),i=Math.max(...t)-e||1,r=s[0].time,o=s[s.length-1].time-r||1,n=s.map(t=>`${((t.time-r)/o*300).toFixed(1)},${(66-(t.value-e)/i*62).toFixed(1)}`);a=L`<svg class="line" viewBox="0 0 300 70" preserveAspectRatio="none">${V`<polyline points=${n.join(" ")}></polyline>`}</svg>`}const r=this.currentKey();return L`<div class="form">
        <label>${t("b_start")}<input type="number" min="0" max="511" .value=${String(e.start)}
          @change=${t=>this.setSpec({start:Math.max(0,parseInt(Lt(t))||0)})} /></label>
        <label>${t("b_length")}<input type="number" min="1" max="64" .value=${String(e.length)}
          @change=${t=>this.setSpec({length:Math.min(64,Math.max(1,parseInt(Lt(t))||1))})} /></label>
        <label>&nbsp;<select @change=${t=>this.setSpec({byte_order:Lt(t)})}>
          <option value="little" ?selected=${"little"===e.byte_order}>${t("b_little")}</option>
          <option value="big" ?selected=${"big"===e.byte_order}>${t("b_big")}</option>
        </select></label>
        <label class="toggle" style="flex-direction:row;align-items:center"><input type="checkbox" .checked=${e.signed}
          @change=${t=>this.setSpec({signed:t.target.checked})} />${t("b_signed")}</label>
        <label>${t("b_factor")}<input type="number" step="any" .value=${String(e.factor)}
          @change=${t=>this.setSpec({factor:this.parse(Lt(t))??1})} /></label>
        <label>${t("b_offset")}<input type="number" step="any" .value=${String(e.offset)}
          @change=${t=>this.setSpec({offset:this.parse(Lt(t))??0})} /></label>
        <button class="primary" ?disabled=${null===r} @click=${()=>null!==r&&this.openAdd(r,e)}>${t("f_add")}</button>
      </div>
      ${i?L`<div class="muted">${t("b_try",{n:i.frames,d:i.distinct_values,c:i.changes,min:jt(i.min),max:jt(i.max),last:jt(i.last)})}</div>${a}`:K}`}openAdd(t,e){const i=this.live?this.source:this.interfaces[0]?.id??"",s=this.interfaces.find(t=>t.id===i);this.add={key:t,spec:{start:e.start,length:e.length,byte_order:e.byte_order,signed:e.signed,factor:e.factor,offset:e.offset},name:"",unit:e.unit??"",entryId:i,deviceId:"",deviceName:`${s?.name??""} ${Vt(t%vt)}`.trim()},this.updateComplete.then(()=>this.renderRoot.querySelector(".addbox")?.scrollIntoView({behavior:"smooth"}))}async submitAdd(){const t=this.add;t&&(t.name.trim()?await this.run(async()=>{const e=t.deviceId?{device_id:t.deviceId}:{device_name:t.deviceName},i=await this.api.addSignal(t.entryId,t.key,{...t.spec,name:t.name.trim(),unit:t.unit.trim()},e);this.add=null,this.message={ok:!0,text:this.t("a_added",{signal:t.name.trim(),device:i.name})}}):this.message={ok:!1,text:this.t("a_name_needed")})}renderAdd(){const t=this.t,e=this.add;if(!e)return K;const i=t=>this.add={...e,...t},s=this.devices.filter(t=>t.interface===e.entryId);return L`<div class="card addbox">
      <h2>${t("a_title")}</h2>
      <div class="muted mono">${Vt(e.key)} · ${t("f_field",{start:e.spec.start,length:e.spec.length})}
        · ${"big"===e.spec.byte_order?"BE":"LE"}${e.spec.signed?` · ${t("f_signed")}`:""}
        ${1!==e.spec.factor?` · × ${e.spec.factor}`:""}${e.spec.offset?` · + ${e.spec.offset}`:""}</div>
      <div class="form">
        <label>${t("a_name")}<input .value=${e.name} @input=${t=>i({name:Lt(t)})} /></label>
        <label>${t("b_unit")}<input style="width:70px" .value=${e.unit} @input=${t=>i({unit:Lt(t)})} /></label>
        <label>${t("a_interface")}<select @change=${t=>i({entryId:Lt(t),deviceId:""})}>
          ${this.interfaces.map(t=>L`<option value=${t.id} ?selected=${t.id===e.entryId}>${t.name}</option>`)}
        </select></label>
        <label>${t("a_device")}<select @change=${t=>i({deviceId:Lt(t)})}>
          <option value="" ?selected=${!e.deviceId}>${t("a_new_device")}</option>
          ${s.map(t=>L`<option value=${t.id} ?selected=${t.id===e.deviceId}>${t.name}</option>`)}
        </select></label>
        ${e.deviceId?K:L`<label>${t("a_device_name")}<input .value=${e.deviceName}
          @input=${t=>i({deviceName:Lt(t)})} /></label>`}
        <button class="primary" ?disabled=${this.busy||!e.entryId} @click=${()=>this.submitAdd()}>${t("a_add")}</button>
        <button class="link" @click=${()=>this.add=null}>${t("cancel")}</button>
      </div>
    </div>`}render(){const t=this.t;return L`
      <div class="muted" style="margin:0 4px 8px">${t("an_source",{name:this.sourceName})}</div>
      ${this.message?L`<div class="card"><div class="chip ${this.message.ok?"ok":"bad"}" style="white-space:normal">${this.message.text}</div></div>`:K}
      ${this.renderAdd()}
      ${this.renderGuided()}
      ${this.renderFind()}
      ${this.renderBits()}`}}qt.styles=[Rt,o`
      .phase {
        font-size: 1.3em;
        margin: 10px 0 4px;
      }
      .steps {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin: 8px 0;
      }
      .hint-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
        margin: 4px 0;
      }
      .result {
        border-top: 1px solid var(--divider-color, #eee);
        padding: 8px 0;
      }
      .wrap {
        overflow-x: auto;
      }
      .cand {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 4px 14px;
        padding: 6px 0;
        border-bottom: 1px solid var(--divider-color, #eee);
      }
      .cand .val {
        min-width: 60px;
      }
      .grid {
        display: inline-grid;
        grid-template-columns: auto repeat(8, minmax(22px, 30px)) auto;
        gap: 2px;
        align-items: center;
        margin: 8px 0;
      }
      .grid .lbl {
        font-size: 0.75em;
        color: var(--secondary-text-color);
        padding-right: 4px;
        white-space: nowrap;
      }
      .cell {
        height: 28px;
        border: 1px solid var(--divider-color, #ddd);
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75em;
        cursor: pointer;
        user-select: none;
        font-variant-numeric: tabular-nums;
      }
      .cell.sel {
        outline: 2px solid var(--primary-color);
        outline-offset: -2px;
        font-weight: 600;
      }
      .cell.anchor {
        outline: 2px dashed var(--primary-color);
      }
      .form {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 12px;
        align-items: end;
        margin: 8px 0;
      }
      .form label {
        display: flex;
        flex-direction: column;
        font-size: 0.85em;
        color: var(--secondary-text-color);
        gap: 2px;
      }
      .form input[type="number"] {
        width: 90px;
      }
      svg.line {
        width: 100%;
        height: 70px;
        display: block;
      }
      svg.line polyline {
        fill: none;
        stroke: var(--primary-color);
        stroke-width: 1.5;
        vector-effect: non-scaling-stroke;
      }
      .addbox {
        border: 1px solid var(--primary-color);
        border-radius: 8px;
        padding: 10px 12px;
        margin: 10px 0;
      }
    `],t([ut({attribute:!1})],qt.prototype,"interfaces",void 0),t([ut({attribute:!1})],qt.prototype,"offline",void 0),t([ut({attribute:!1})],qt.prototype,"devices",void 0),t([ut({attribute:!1})],qt.prototype,"source",void 0),t([ut({attribute:!1})],qt.prototype,"focusId",void 0),t([ut({attribute:!1})],qt.prototype,"t",void 0),t([ut({attribute:!1})],qt.prototype,"api",void 0),t([mt()],qt.prototype,"message",void 0),t([mt()],qt.prototype,"busy",void 0),t([mt()],qt.prototype,"guided",void 0),t([mt()],qt.prototype,"tick",void 0),t([mt()],qt.prototype,"find",void 0),t([mt()],qt.prototype,"findValue",void 0),t([mt()],qt.prototype,"findTol",void 0),t([mt()],qt.prototype,"idText",void 0),t([mt()],qt.prototype,"tx",void 0),t([mt()],qt.prototype,"bits",void 0),t([mt()],qt.prototype,"spec",void 0),t([mt()],qt.prototype,"ends",void 0),t([mt()],qt.prototype,"anchor",void 0),t([mt()],qt.prototype,"trial",void 0),t([mt()],qt.prototype,"add",void 0),St("woow-can-analyze",qt);class Kt extends lt{constructor(){super(...arguments),this.interfaces=[],this.offline=[],this.files=[],this.message=null,this.deleting="",this.busy=!1,this.format="log"}async run(t,e){this.busy=!0;try{await t(),this.message=e?{ok:!0,text:e}:null}catch(t){this.message={ok:!1,text:this.t("error",{msg:kt(t)})}}finally{this.busy=!1}}changed(){this.dispatchEvent(new CustomEvent("captures-changed"))}async upload(t){const e=t.target,i=e.files?.[0];e.value="",i&&await this.run(async()=>{const t=await this.api.upload(i);this.message={ok:!0,text:this.t("uploaded",{name:t})},this.changed()})}ext(t){const e=t.lastIndexOf(".");return e<0?"":t.slice(e+1).toLowerCase()}formatName(t){const e=`fmt_${t}`;return Nt(e)?this.t(e):t}async convert(t){await this.run(async()=>{const e=await this.api.capture("convert",{name:t,format:this.format});this.message={ok:!0,text:this.t("converted",{name:e.name??"",n:(e.frames??0).toLocaleString()})},this.changed()})}formatPicker(){const t=this.t;return L`<label class="row" style="gap:6px">
      <span class="muted">${t("file_format")}</span>
      <select .value=${this.format} @change=${t=>this.format=t.target.value}>
        ${ft.map(e=>L`<option value=${e} ?selected=${e===this.format}>${t(`fmt_${e}`)}</option>`)}
      </select>
    </label>`}async open(t){await this.run(async()=>{const e=await this.api.capture("open",{name:t}),i=e.sources?.[0];i&&this.dispatchEvent(new CustomEvent("open-source",{detail:i.id}))},this.t("opened"))}render(){const t=this.t;return L`<div class="card">
        <div class="row">
          <h2 class="grow">${t("capture_title")}</h2>
          ${this.formatPicker()}
        </div>
        <div class="muted">${t("capture_hint")}</div>
        ${"csv"===this.format?L`<div class="muted" style="margin-top:4px">${t("csv_note")}</div>`:K}
        <div class="ifaces" style="margin-top:12px">
          ${this.interfaces.map(e=>L`<div class="row">
            <b>${e.name}</b><span class="muted">${e.port}</span>
            <span class="grow"></span>
            ${e.recording?L`<span class="chip bad">● ${t("recording",{n:e.recording.frames.toLocaleString(),size:Ot(e.recording.bytes)})}</span>
                  <button ?disabled=${this.busy} @click=${()=>this.run(async()=>{await this.api.capture("stop",{entry_id:e.id}),this.changed()})}>${t("stop_record")}</button>`:L`<button class="primary" ?disabled=${this.busy} @click=${()=>this.run(async()=>{await this.api.capture("start",{entry_id:e.id}),this.changed()})}>${t("record")}</button>`}
            <button title=${t("export_hint",{n:(e.trace.end-e.trace.first).toLocaleString()})}
              @click=${()=>this.run(()=>this.api.download(`/api/woow_can/export/${e.id}?format=${this.format}`))}>${t("export")}</button>
          </div>`)}
        </div>
        ${this.message?L`<div class="chip ${this.message.ok?"ok":"bad"}" style="margin-top:10px;white-space:normal">${this.message.text}</div>`:K}
      </div>
      <div class="card">
        <div class="row">
          <h2 class="grow">${t("files_title")}</h2>
          <label><button title=${t("upload_hint")} @click=${()=>this.renderRoot.querySelector("#upload")?.click()}>
            ${t("upload")}</button></label>
          <input id="upload" type="file" accept=".log,.txt,.asc,.csv,.trc,.crtd,.pcap" @change=${this.upload} />
        </div>
        ${0===this.files.length?L`<div class="empty">${t("files_empty")}</div>`:L`<div class="wrap"><table>
              <tbody>
                ${this.files.map(e=>L`<tr>
                  <td class="mono">${e.recording?L`<span class="chip bad">●</span> `:K}${e.name}</td>
                  <td class="num">${Ot(e.size)}</td>
                  <td class="muted">${Mt(e.modified,t)}</td>
                  <td class="row">
                    <button class="link" @click=${()=>this.run(()=>this.api.download(`/api/woow_can/captures/${encodeURIComponent(e.name)}`))}>${t("download")}</button>
                    <button class="link" ?disabled=${e.recording} @click=${()=>this.open(e.name)}>${t("open")}</button>
                    <button class="link" ?disabled=${e.recording||this.busy||this.ext(e.name)===this.format}
                      title=${t("convert_hint",{fmt:t(`fmt_${this.format}`)})}
                      @click=${()=>this.convert(e.name)}>${t("convert")} → ${this.format.toUpperCase()}</button>
                    ${this.deleting===e.name?L`<span>${t("delete_confirm",{name:e.name})}</span>
                          <button class="danger" @click=${()=>this.run(async()=>{this.deleting="",await this.api.capture("delete",{name:e.name}),this.changed()})}>${t("delete")}</button>
                          <button @click=${()=>this.deleting=""}>${t("cancel")}</button>`:L`<button class="link danger" ?disabled=${e.recording} @click=${()=>this.deleting=e.name}>
                          ${t("delete")}</button>`}
                  </td>
                </tr>`)}
              </tbody>
            </table></div>`}
        ${this.offline.length?L`<h2 style="margin-top:16px">${t("offline_title")}</h2>
              ${this.offline.map(e=>L`<div class="row">
                <span class="mono grow">${e.name}</span>
                <span class="muted">${e.format&&"log"!==e.format?`${this.formatName(e.format)} · `:""}${e.frames.toLocaleString()}${e.truncated?` · ${t("truncated",{n:e.frames})}`:""}</span>
                <button class="link" @click=${()=>this.dispatchEvent(new CustomEvent("open-source",{detail:e.id}))}>
                  ${t("tab_monitor")}</button>
                <button class="link" @click=${()=>this.run(()=>this.api.capture("close",{source:e.id}))}>${t("close")}</button>
              </div>`)}`:K}
      </div>`}}Kt.styles=[Rt,o`
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
    `],t([ut({attribute:!1})],Kt.prototype,"interfaces",void 0),t([ut({attribute:!1})],Kt.prototype,"offline",void 0),t([ut({attribute:!1})],Kt.prototype,"files",void 0),t([ut({attribute:!1})],Kt.prototype,"t",void 0),t([ut({attribute:!1})],Kt.prototype,"api",void 0),t([mt()],Kt.prototype,"message",void 0),t([mt()],Kt.prototype,"deleting",void 0),t([mt()],Kt.prototype,"busy",void 0),t([mt()],Kt.prototype,"format",void 0),St("woow-can-capture",Kt);const Gt=2;let Jt=class{constructor(t){}get _$AU(){return this._$AM._$AU}_$AT(t,e,i){this._$Ct=t,this._$AM=e,this._$Ci=i}_$AS(t,e){return this.update(t,e)}update(t,e){return this.render(...e)}};const{I:Zt}=ot,Xt=t=>t,Qt=()=>document.createComment(""),Yt=(t,e,i)=>{const s=t._$AA.parentNode,a=void 0===e?t._$AB:e._$AA;if(void 0===i){const e=s.insertBefore(Qt(),a),r=s.insertBefore(Qt(),a);i=new Zt(e,r,t,t.options)}else{const e=i._$AB.nextSibling,r=i._$AM,o=r!==t;if(o){let e;i._$AQ?.(t),i._$AM=t,void 0!==i._$AP&&(e=t._$AU)!==r._$AU&&i._$AP(e)}if(e!==a||o){let t=i._$AA;for(;t!==e;){const e=Xt(t).nextSibling;Xt(s).insertBefore(t,a),t=e}}}return i},te=(t,e,i=t)=>(t._$AI(e,i),t),ee={},ie=(t,e=ee)=>t._$AH=e,se=t=>{t._$AR(),t._$AA.remove()},ae=(t,e,i)=>{const s=new Map;for(let a=e;a<=i;a++)s.set(t[a],a);return s},re=(t=>(...e)=>({_$litDirective$:t,values:e}))(class extends Jt{constructor(t){if(super(t),t.type!==Gt)throw Error("repeat() can only be used in text expressions")}dt(t,e,i){let s;void 0===i?i=e:void 0!==e&&(s=e);const a=[],r=[];let o=0;for(const e of t)a[o]=s?s(e,o):o,r[o]=i(e,o),o++;return{values:r,keys:a}}render(t,e,i){return this.dt(t,e,i).values}update(t,[e,i,s]){const a=(t=>t._$AH)(t),{values:r,keys:o}=this.dt(e,i,s);if(!Array.isArray(a))return this.ut=o,r;const n=this.ut??=[],c=[];let l,d,h=0,p=a.length-1,u=0,m=r.length-1;for(;h<=p&&u<=m;)if(null===a[h])h++;else if(null===a[p])p--;else if(n[h]===o[u])c[u]=te(a[h],r[u]),h++,u++;else if(n[p]===o[m])c[m]=te(a[p],r[m]),p--,m--;else if(n[h]===o[m])c[m]=te(a[h],r[m]),Yt(t,c[m+1],a[h]),h++,m--;else if(n[p]===o[u])c[u]=te(a[p],r[u]),Yt(t,a[h],a[p]),p--,u++;else if(void 0===l&&(l=ae(o,u,m),d=ae(n,h,p)),l.has(n[h]))if(l.has(n[p])){const e=d.get(o[u]),i=void 0!==e?a[e]:null;if(null===i){const e=Yt(t,a[h]);te(e,r[u]),c[u]=e}else c[u]=te(i,r[u]),Yt(t,a[h],i),a[e]=null;u++}else se(a[p]),p--;else se(a[h]),h++;for(;u<=m;){const e=Yt(t,c[m+1]);te(e,r[u]),c[u++]=e}for(;h<=p;){const t=a[h++];null!==t&&se(t)}return this.ut=o,ie(t,c),q}}),oe=2e3,ne={rise:"#00bbff",fall:"#ff3b30",churn:"#6656a9"},ce=()=>({t:-1e9,dir:0,same:0,kind:"",bitT:new Array(8).fill(-1e9),notch:0});function le(t){const e=[];for(let i=0;i+1<t.length;i+=2)e.push(parseInt(t.slice(i,i+2),16));return e}const de=t=>t.target.value;class he extends lt{constructor(){super(...arguments),this.interfaces=[],this.offline=[],this.source="",this.paused=!1,this.bin=!1,this.filterText="",this.changingOnly=!1,this.hideInactive=!1,this.expanded=-1,this.message="",this.trace=[],this.traceNext=null,this.traceBusy=!1,this.traceDir="",this.frames=0,this.overflow=0,this.tick=0,this.narrow=!1,this.decoded=null,this.rows=new Map,this.names=new Map,this.decodedAt=0,this.decodedKey=-1,this.order=[],this.orderDirty=!0,this.pins=new Set,this.token="",this.subscribed="",this.serverOffset=0,this.traceEnd=null,this.resize=new ResizeObserver(t=>{const e=t[0]?.contentRect.width??1e3;e<640!==this.narrow&&(this.narrow=e<640)}),this.onVisibility=()=>{document.hidden?this.stop():this.paused||this.start()}}connectedCallback(){super.connectedCallback(),document.addEventListener("visibilitychange",this.onVisibility),this.resize.observe(this),this.timer=window.setInterval(()=>{this.paused||document.hidden||(this.tick++,this.expanded>=0&&performance.now()-this.decodedAt>1e3&&this.refreshDecode())},200),this.loadPins(),this.source&&!this.paused&&this.start()}disconnectedCallback(){super.disconnectedCallback(),document.removeEventListener("visibilitychange",this.onVisibility),this.resize.disconnect(),window.clearInterval(this.timer),window.clearTimeout(this.retry),this.stop()}updated(t){t.has("source")&&this.source!==this.subscribed&&(this.paused=!1,this.trace=[],this.loadPins(),this.start())}get live(){return this.interfaces.some(t=>t.id===this.source)}get iface(){return this.interfaces.find(t=>t.id===this.source)}loadPins(){this.pins=new Set(At(`woow_can.pins.${this.source}`,[])),this.orderDirty=!0}savePins(){Ct(`woow_can.pins.${this.source}`,[...this.pins])}async start(){if(await this.stop(),!this.source||document.hidden)return;const t=this.source;this.rows.clear(),this.orderDirty=!0,this.token=Math.random().toString(36).slice(2,12)+Date.now().toString(36);const e=this.token;this.subscribed=t;try{const i=await this.api.subscribeMonitor(t,e,t=>this.onBatch(t,e));if(this.token!==e)return void i();this.unsub=i}catch(t){this.message=kt(t)}}async stop(){const t=this.unsub;if(this.unsub=void 0,this.token="",t)try{await t()}catch{}}onBatch(t,e){if(e!==this.token)return;if(t.gone)return this.message=t.error??this.t("gone"),window.clearTimeout(this.retry),void(this.retry=window.setTimeout(()=>!this.paused&&void this.start(),1500));const i=performance.now();this.serverOffset=t.t-Date.now()/1e3,(t.full||t.clear)&&(this.rows.clear(),this.orderDirty=!0),t.full&&this.names.clear();for(const[e,i]of Object.entries(t.names??{}))this.names.set(Number(e)%vt,i);for(const e of t.rows??[])this.applyRow(e,i,!!t.full);void 0!==t.frames&&(this.frames=t.frames),void 0!==t.overflow&&(this.overflow=t.overflow),void 0!==t.trace_end&&(this.traceEnd=t.trace_end),this.message===this.t("gone")&&(this.message=""),t.seq>0&&this.api.ack(e,t.seq).catch(()=>{})}applyRow(t,e,i){const[s,a,r,o,n,c,l,d,h,p,u,m]=t,f=le(o);let _=this.rows.get(s);if(_){if(h){const t=c?c/1e6:1;for(let i=0;i<f.length;i++){const s=parseInt(h.slice(2*i,2*i+2)||"0",16);if(!s)continue;const a=_.b[i]??=ce();for(let t=0;t<8;t++)s>>t&1&&(a.bitT[t]=e);if(!(s&~a.notch&255))continue;const r=_.bytes[i]??0,o=f[i]>r?1:f[i]<r?-1:0,n=e-a.t>10*t*1e3;a.same=0!==o&&o===a.dir?a.same+1:1,a.dir=o,a.kind=0===o?"churn":n||a.same>8?o>0?"rise":"fall":"churn",a.t=e}_.b.length!==f.length&&(_.b=f.map((t,e)=>_.b[e]??ce()))}}else _={key:s,raw:a,flags:r,hex:o,bytes:f,count:n,period:0,pmin:0,pmax:0,last:p,changed:u,changedPrev:m,born:i?0:e,b:f.map(()=>ce())},this.rows.set(s,_),this.orderDirty=!0;Object.assign(_,{raw:a,flags:r,hex:o,bytes:f,count:n,last:p,changed:u,changedPrev:m,period:c/1e6,pmin:l/1e6,pmax:d/1e6})}serverNow(){return Date.now()/1e3+this.serverOffset}notch(){const t=performance.now();let e=0;for(const i of this.rows.values())for(const s of i.b)s.bitT.forEach((i,a)=>{t-i<2e3&&!(s.notch>>a&1)&&(s.notch|=1<<a,e++)});this.message=e?this.t("notch_added",{n:e}):this.t("notch_none")}clearNotch(){for(const t of this.rows.values())for(const e of t.b)e.notch=0;this.message=""}async clear(){try{await this.api.clearMonitor(this.source)}catch(t){this.message=kt(t)}}async pause(t){void 0!==t&&(this.filterText=t),this.paused=!0,await this.stop(),this.trace=[],this.traceNext=this.traceEnd,await this.loadTrace(!0)}resume(){this.paused=!1,this.trace=[],this.start()}async loadTrace(t=!1){if(!this.traceBusy){this.traceBusy=!0;try{const e=new yt(this.filterText),i=await this.api.trace(this.source,{before:t?this.traceEnd:this.traceNext,limit:200,ids:e.error||e.all?"":this.filterText,direction:this.traceDir||null});this.trace=t?i.frames:[...this.trace,...i.frames],this.traceNext=i.next}catch(t){this.message=kt(t)}finally{this.traceBusy=!1}}}async refreshDecode(){const t=this.rows.get(this.expanded);if(this.decodedAt=performance.now(),!t||16&t.flags)this.decoded=null;else{this.decodedKey!==t.key&&(this.decoded=null),this.decodedKey=t.key;try{const e=await this.api.decode(this.source,t.raw,t.hex);this.expanded===t.key&&(this.decoded=e.decoded)}catch{this.decoded=null}}}toggleRow(t){this.expanded=this.expanded===t?-1:t,this.decoded=null,this.decodedAt=0,this.expanded>=0&&this.refreshDecode()}togglePin(t){this.pins.has(t)?this.pins.delete(t):this.pins.add(t),this.pins=new Set(this.pins),this.savePins(),this.orderDirty=!0,this.requestUpdate()}sendAgain(t){this.dispatchEvent(new CustomEvent("send-frame",{detail:{frame:$t(t.raw,t.flags,t.hex),entryId:this.live?this.source:""}}))}async fireEvents(t){const e=this.iface;if(!e)return;const i=bt(t.raw),s=e.settings.event_filter.trim();try{await this.api.setEvents(e.id,s?`${s}, ${i}`:i),this.message=this.t("events_added",{id:i})}catch(t){this.message=kt(t)}}notchRow(t){for(const e of t.b)e.notch=255;this.requestUpdate()}sorted(){return this.orderDirty&&(this.order=[...this.rows.values()].sort((t,e)=>{const i=this.pins.has(t.key)?0:1,s=this.pins.has(e.key)?0:1;if(i!==s)return i-s;const a=gt(t.raw)?1:0,r=gt(e.raw)?1:0;if(a!==r)return a-r;const o=t.raw%536870912,n=e.raw%536870912;return o!==n?o-n:t.key-e.key}).map(t=>t.key),this.orderDirty=!1),this.order.map(t=>this.rows.get(t)).filter(t=>!!t)}byteCells(t,e){return t.bytes.map((i,s)=>{const a=t.b[s];let r="";if(a?.kind){const t=Math.max(0,1-(e-a.t)/oe)*("churn"===a.kind?.4:.65);t>.01&&(r=`background: color-mix(in srgb, ${ne[a.kind]} ${Math.round(100*t)}%, transparent)`)}const o=this.bin?i.toString(2).padStart(8,"0"):i.toString(16).toUpperCase().padStart(2,"0");return L`<span class="byte ${this.bin?"bin":""} ${a?.notch?"notched":""}" style=${r}>${o}</span>`})}detailRow(t,e){return L`<tr class="detail"><td colspan="9">${this.detail(t,e)}</td></tr>`}detail(t,e){const i=this.t,s=this.pins.has(t.key),a=this.iface,r=a?new yt(a.settings.event_filter):null,o=!!(a&&a.settings.event_filter.trim()&&r&&!r.error&&r.matches(t.raw)),n=this.decodedKey===t.key?this.decoded:null;return L`
        <div class="mono">${$t(t.raw,t.flags,t.hex)}</div>
        ${null===n?K:0===n.length?L`<div class="muted">${i("no_definition")}</div>`:n.map(t=>L`<div class="decoded">
                <span class="muted">${t.source} · ${t.message}</span>
                ${t.signals.map(t=>L`<span class="sig">${t.name} <b>${jt(t.value,t.unit)}</b></span>`)}
              </div>`)}
        <div class="muted">
          ${t.period?L`${i("detail_period",{avg:(1e3*t.period).toFixed(t.period<.1?2:1),min:(1e3*t.pmin).toFixed(1),max:(1e3*t.pmax).toFixed(1)})} · ${i("detail_rate",{hz:(1/t.period).toFixed(2)})}`:K}
        </div>
        ${t.changedPrev?L`<div class="muted">
              ${i("detail_changed",{ago:Mt(t.changed,i,e),gap:zt(t.changed-t.changedPrev)})}
            </div>`:K}
        <div class="actions">
          <button @click=${()=>this.togglePin(t.key)}>${i(s?"row_unpin":"row_pin")}</button>
          <button @click=${()=>this.sendAgain(t)}>${i("row_send")}</button>
          ${a?L`<button ?disabled=${o} @click=${()=>this.fireEvents(t)}>
                ${i(o?"row_events_on":"row_events")}
              </button>`:K}
          <button @click=${()=>this.pause(bt(t.raw))}>${i("row_trace")}</button>
          <button @click=${()=>this.notchRow(t)}>${i("row_notch")}</button>
          <button @click=${()=>this.dispatchEvent(new CustomEvent("analyze-id",{detail:t.key}))}>${i("row_analyze")}</button>
        </div>`}renderLive(){const t=this.t,e=performance.now(),i=this.serverNow(),s=new yt(this.filterText),a=this.sorted().filter(t=>!(!s.error&&!s.matches(t.raw))&&((!this.changingOnly||t.changedPrev>0&&i-t.changed<5)&&!(this.hideInactive&&i-t.last>5)));return this.rows.size?this.narrow?this.renderCards(a,e,i):L`<div class="wrap">
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
          ${re(a,t=>t.key,s=>{const a=i-s.last,r=a>(s.period?5*s.period+.5:1.75),o=s.key>=vt,n=!o&&!!(8&s.flags)&&!this.iface?.virtual;return L`<tr class="${r?"inactive":""} ${s.born&&e-s.born<oe?"new":""}">
                  <td><button class="pin ${this.pins.has(s.key)?"on":""}" title=${t("row_pin")}
                    @click=${()=>this.togglePin(s.key)}>${this.pins.has(s.key)?"★":"☆"}</button></td>
                  <td class="id ${a>4?"stale":""}" @click=${()=>this.toggleRow(s.key)}>
                    ${bt(s.raw)}${o?L`<span class="tag">${t("dir_tx")}</span>`:K}${n?L`<span class="tag muted-tag">${t("dir_local")}</span>`:K}${this.names.has(s.key%vt)?L`<div class="name">${this.names.get(s.key%vt)}</div>`:K}
                  </td>
                  <td class="num">${s.bytes.length}</td>
                  <td><div class="bytes">${this.byteCells(s,e)}</div></td>
                  <td class="num">${s.count.toLocaleString()}</td>
                  <td class="num">${s.period?(1/s.period).toFixed(1):"–"}</td>
                  <td class="num">${s.period?zt(s.period):"–"}</td>
                  <td class="num">${s.changedPrev?zt(s.changed-s.changedPrev):"–"}</td>
                  <td class="num">${zt(Math.max(0,a))}</td>
                </tr>
                ${this.expanded===s.key?this.detailRow(s,i):K}`})}
        </tbody>
      </table>
    </div>`:L`<div class="empty">${t("monitor_empty")}</div>`}renderCards(t,e,i){const s=this.t;return L`<div class="cards">
      ${re(t,t=>t.key,t=>{const a=i-t.last,r=a>(t.period?5*t.period+.5:1.75),o=t.key>=vt;return L`<div class="mrow ${r?"inactive":""} ${t.born&&e-t.born<oe?"new":""}">
            <div class="mhead" @click=${()=>this.toggleRow(t.key)}>
              <button class="pin ${this.pins.has(t.key)?"on":""}" @click=${e=>{e.stopPropagation(),this.togglePin(t.key)}}>${this.pins.has(t.key)?"★":"☆"}</button>
              <span class="id ${a>4?"stale":""}">${bt(t.raw)}</span>
              ${o?L`<span class="tag">${s("dir_tx")}</span>`:K}
              ${this.names.has(t.key%vt)?L`<span class="muted">${this.names.get(t.key%vt)}</span>`:K}
              <span class="grow"></span>
              <span class="muted">${t.period?`${(1/t.period).toFixed(1)} Hz · `:""}${zt(Math.max(0,a))}</span>
            </div>
            <div class="bytes wrapbytes">${this.byteCells(t,e)}</div>
            ${this.expanded===t.key?L`<div class="mdetail">${this.detail(t,i)}</div>`:K}
          </div>`})}
    </div>`}renderTrace(){const t=this.t,e=this.trace;return L`<div class="row msg">
        <b class="grow">${t("paused_title")}</b>
        <select @change=${t=>{this.traceDir=de(t),this.loadTrace(!0)}}>
          <option value="" ?selected=${!this.traceDir}>${t("trace_all_dirs")}</option>
          <option value="rx" ?selected=${"rx"===this.traceDir}>${t("dir_rx")}</option>
          <option value="tx" ?selected=${"tx"===this.traceDir}>${t("dir_tx")}</option>
        </select>
      </div>
      ${0===e.length?L`<div class="empty">${this.traceBusy?t("loading"):t("trace_empty")}</div>`:L`<div class="wrap">
            <table>
              <thead>
                <tr>
                  <th>${t("trace_time")}</th>
                  ${this.narrow?K:L`<th class="num">${t("trace_delta")}</th>`}
                  <th>${t("col_dir")}</th>
                  <th>${t("col_id")}</th>
                  ${this.narrow?K:L`<th>${t("col_len")}</th>`}
                  <th>${t("col_data")}</th>
                </tr>
              </thead>
              <tbody>
                ${e.map(([i,s,a,r,o],n)=>{const c=e[n+1],l=!!(16&r),d=!!(4&r);return L`<tr title=${`#${i}`}>
                    <td class="num">${Tt(s)}</td>
                    ${this.narrow?K:L`<td class="num">${c?zt(s-c[1]):""}</td>`}
                    <td>${t(d?"dir_tx":"dir_rx")}</td>
                    <td class="id">${l?L`<span class="tag err">ERR</span>`:bt(a)}</td>
                    ${this.narrow?K:L`<td class="num">${o.length/2}</td>`}
                    <td><div class="bytes">
                      ${l?L`<span class="muted">${t("trace_error",{x:$t(a,r,o)})}</span>`:le(o).map(t=>L`<span class="byte ${this.bin?"bin":""}">${this.bin?t.toString(2).padStart(8,"0"):t.toString(16).toUpperCase().padStart(2,"0")}</span>`)}
                    </div></td>
                  </tr>`})}
              </tbody>
            </table>
          </div>`}
      <div class="row msg">
        ${null!==this.traceNext?L`<button ?disabled=${this.traceBusy} @click=${()=>this.loadTrace()}>${t("trace_older")}</button>`:e.length?L`<span class="muted">${t("trace_start")}</span>`:K}
      </div>`}render(){const t=this.t;this.tick;const e=this.offline.find(t=>t.id===this.source),i=new yt(this.filterText);return L`<div class="card">
      <div class="toolbar">
        <select title=${t("source")} @change=${t=>this.dispatchEvent(new CustomEvent("source-changed",{detail:de(t)}))}>
          ${this.interfaces.map(t=>L`<option value=${t.id} ?selected=${t.id===this.source}>${t.name} · ${t.port}</option>`)}
          ${this.offline.map(e=>L`<option value=${e.id} ?selected=${e.id===this.source}>${t("file_source",{name:e.name})}</option>`)}
        </select>
        ${this.paused?L`<button class="primary" @click=${()=>this.resume()}>${t("resume")}</button>`:L`<button @click=${()=>this.pause()}>${t("pause")}</button>`}
        ${this.live&&!this.paused?L`<button @click=${()=>this.clear()}>${t("clear")}</button>`:K}
        ${this.paused?K:L`<button @click=${()=>this.notch()}>${t("notch")}</button>
              <button @click=${()=>this.clearNotch()}>${t("notch_clear")}</button>
              <label class="toggle"><input type="checkbox" .checked=${this.changingOnly}
                @change=${t=>this.changingOnly=t.target.checked} />${t("changing_only")}</label>
              <label class="toggle"><input type="checkbox" .checked=${this.hideInactive}
                @change=${t=>this.hideInactive=t.target.checked} />${t("hide_inactive")}</label>`}
        <label class="toggle"><input type="checkbox" .checked=${this.bin}
          @change=${t=>this.bin=t.target.checked} />${t("view_bin")}</label>
        <input type="search" placeholder=${t("filter_ph")} .value=${this.filterText}
          @input=${t=>this.filterText=de(t)}
          @change=${()=>this.paused&&this.loadTrace(!0)} />
      </div>
      ${i.error?L`<div class="chip bad">${t("filter_bad",{x:i.error})}</div>`:K}
      <div class="muted">
        ${t("frames_total",{ids:this.rows.size,n:this.frames.toLocaleString()})}
        ${this.overflow?L` · ${t("overflow",{n:this.overflow})}`:K}
        ${e?L` · ${t("offline_note",{file:e.file,n:e.frames})}`:K}
      </div>
      ${this.message?L`<div class="msg chip info" style="white-space:normal">${this.message}</div>`:K}
      ${this.paused?this.renderTrace():this.renderLive()}
      ${this.paused?K:L`<p class="muted">${t("monitor_hint")}</p>`}
    </div>`}}he.styles=[Rt,Ft,o`
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
    `],t([ut({attribute:!1})],he.prototype,"interfaces",void 0),t([ut({attribute:!1})],he.prototype,"offline",void 0),t([ut({attribute:!1})],he.prototype,"source",void 0),t([ut({attribute:!1})],he.prototype,"t",void 0),t([ut({attribute:!1})],he.prototype,"api",void 0),t([mt()],he.prototype,"paused",void 0),t([mt()],he.prototype,"bin",void 0),t([mt()],he.prototype,"filterText",void 0),t([mt()],he.prototype,"changingOnly",void 0),t([mt()],he.prototype,"hideInactive",void 0),t([mt()],he.prototype,"expanded",void 0),t([mt()],he.prototype,"message",void 0),t([mt()],he.prototype,"trace",void 0),t([mt()],he.prototype,"traceNext",void 0),t([mt()],he.prototype,"traceBusy",void 0),t([mt()],he.prototype,"traceDir",void 0),t([mt()],he.prototype,"frames",void 0),t([mt()],he.prototype,"overflow",void 0),t([mt()],he.prototype,"tick",void 0),t([mt()],he.prototype,"narrow",void 0),t([mt()],he.prototype,"decoded",void 0),St("woow-can-monitor",he);const pe={error_active:"ok",error_warning:"warn",error_passive:"warn",bus_off:"bad",stopped:"",sleeping:"",virtual:"info"};class ue extends lt{constructor(){super(...arguments),this.interfaces=[],this.history={}}stateLabel(t){if(!t.available)return this.t("unavailable");const e=String(t.status.state??"unknown"),i=`state_${e}`;return Nt(i)?this.t(i):e}sparkline(t){if(t.length<2)return K;const e=Math.max(10,...t),i=300,s=36,a=i/(t.length-1),r=t.map((t,i)=>`${(i*a).toFixed(1)},${(34-t/e*32).toFixed(1)}`);return L`<svg class="spark" viewBox="0 0 ${i} ${s}" preserveAspectRatio="none" role="img" aria-label=${this.t("sparkline")}>
      ${V`<line x1="0" y1=${35} x2=${i} y2=${35}></line>
        <polygon points=${`0,35 ${r.join(" ")} 300,35`}></polygon>
        <polyline points=${r.join(" ")}></polyline>`}
    </svg>`}hints(t){const e=this.t,i=t.status,s=[];return t.settings.listen_only&&!t.virtual&&s.push({cls:"info",text:e("hint_listen_only")}),"bus_off"===i.state?s.push({cls:"bad",text:t.settings.restart_ms?e("hint_bus_off_auto",{ms:t.settings.restart_ms}):e("hint_bus_off_manual")}):"error_passive"===i.state&&Number(i.tx_error_counter??0)>=128&&s.push({cls:"warn",text:e("hint_passive")}),Number(i.rx_over_errors??0)>0&&s.push({cls:"warn",text:e("hint_overflow",{n:Number(i.rx_over_errors)})}),Number(i.socket_drops??0)>0&&s.push({cls:"warn",text:e("hint_socket_drops",{n:Number(i.socket_drops)})}),s}card(t){const e=this.t,i=t.status,s=t.load,a=i.berr_reporting?`${i.bus_error??0} · ${e("arbitration_lost")} ${i.arbitration_lost??0}`:i.berr_supported?e("reporting_off"):e("not_supported"),r=t.virtual?[e("virtual_iface")]:[e("kbps",{n:Math.round(t.settings.bitrate/1e3)}),...t.settings.fd?[e("can_fd")]:[],...t.settings.listen_only?[e("listen_only")]:[]],o=t.errors.last,n=String(i.state??"");return L`<div class="card">
      <div class="head">
        <b>${t.name}</b>
        <span class="muted">${t.port} · ${t.driver||"?"} · ${r.join(" · ")}</span>
        <span class="grow"></span>
        <button class="link" @click=${()=>this.dispatchEvent(new CustomEvent("open-monitor",{detail:t.id}))}>
          ${e("open_monitor")}
        </button>
      </div>
      <div class="row">
        <span class="chip ${t.available?pe[n]??"":"bad"}">${this.stateLabel(t)}</span>
        ${null!=i.tx_error_counter?L`<span class="muted">${e("tec_rec")} ${i.tx_error_counter} / ${i.rx_error_counter}</span>`:K}
        ${t.recording?L`<span class="chip bad">● ${e("recording_now",{name:t.recording.name,n:t.recording.frames})}</span>`:K}
      </div>
      ${this.hints(t).map(t=>L`<div class="hint ${t.cls}">${t.text}</div>`)}
      ${t.virtual?K:L`<div>
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
        ${t.virtual?K:L`<dt>${e("controller_events")}</dt>
              <dd>${i.error_warning??"–"} / ${i.error_passive??"–"} / ${i.bus_off??"–"} / ${i.restarts??"–"}</dd>
              <dt>${e("bus_errors")}</dt>
              <dd>${a}</dd>`}
        <dt>${e("drops")}</dt>
        <dd>${i.socket_drops??0} / ${i.rx_over_errors??0} / ${i.events_dropped??0}</dd>
        <dt>${e("last_error")}</dt>
        <dd>
          ${o?L`<span title=${`${Tt(o.t)} · ${o.frame}`}
                >${o.codes.map(t=>function(t,e){const i=`err_${t}`;return Nt(i)?e(i):t}(t,e)).join("、")} · ${Mt(o.t,e)}</span
              >`:e("none")}
        </dd>
      </dl>
      <div class="muted">
        ${t.settings.event_filter?e("events_filter",{x:t.settings.event_filter}):e("events_none")}
        ${i.clock?L` · ${e("clock_mhz",{n:Number(i.clock)/1e6})}`:K}
        ${i.sample_point?L` · ${e("sample_point",{n:(100*Number(i.sample_point)).toFixed(1)})}`:K}
      </div>
    </div>`}render(){return this.interfaces.length?L`<div class="cards">${this.interfaces.map(t=>this.card(t))}</div>`:L`<div class="card"><div class="empty">${this.t("no_interfaces")}</div></div>`}}ue.styles=[Rt,o`
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
    `],t([ut({attribute:!1})],ue.prototype,"interfaces",void 0),t([ut({attribute:!1})],ue.prototype,"history",void 0),t([ut({attribute:!1})],ue.prototype,"t",void 0),St("woow-can-overview",ue);const me=t=>t.target.value;class fe extends lt{constructor(){super(...arguments),this.interfaces=[],this.periodic=[],this.confirmed=new Set,this.draft=null,this.entryId="",this.frame="",this.waitId="",this.waitMs=0,this.busy=!1,this.result=null,this.confirming=!1,this.edit=null,this.editError="",this.listError="",this.draftSeen=0}willUpdate(t){t.has("draft")&&this.draft&&this.draft.n!==this.draftSeen&&(this.draftSeen=this.draft.n,this.frame=this.draft.frame,this.draft.entryId&&(this.entryId=this.draft.entryId),this.result=null),this.entryId&&this.interfaces.some(t=>t.id===this.entryId)||(this.entryId=(this.interfaces.find(t=>t.can_send)??this.interfaces[0])?.id??"")}get iface(){return this.interfaces.find(t=>t.id===this.entryId)}whyNot(t){return t?t.available?t.can_send?"":this.t("why_listen"):this.t("why_unavailable"):""}trySend(){this.frame.trim()&&this.iface&&(this.confirmed.has(this.entryId)?this.send():this.confirming=!0)}async send(){const t=this.t;this.confirming=!1,this.dispatchEvent(new CustomEvent("confirmed",{detail:this.entryId})),this.busy=!0,this.result=null;try{const e=await this.api.send(this.entryId,this.frame.trim(),this.waitMs,this.waitId.trim());let i=t("sent_ok",{frame:e.sent.frame});(this.waitMs>0||this.waitId)&&(i+="\n"+(e.reply?t("reply",{frame:e.reply.frame}):t("no_reply"))),this.result={ok:!0,text:i}}catch(e){this.result={ok:!1,text:t("error",{msg:kt(e)})}}finally{this.busy=!1}}newDraft(){this.editError="",this.edit={name:"",entry_id:this.entryId,frame:this.frame.trim(),period_ms:1e3,count:0}}async saveDraft(){if(this.edit)try{await this.api.savePeriodic(this.edit),this.edit=null,this.editError=""}catch(t){this.editError=kt(t)}}async control(t,e){this.listError="";try{await this.api.controlPeriodic(t.id,e)}catch(e){this.listError=`${t.name}: ${kt(e)}`}}state(t){const e=this.t;return t.running?e("running"):"count"===t.stopped_by?e("stopped_by_count"):"error"===t.stopped_by?e("stopped_by_error",{x:t.error??"?"}):"interface"===t.stopped_by?e("stopped_by_interface"):e("stopped")}renderEditor(){const t=this.t,e=this.edit;if(!e)return K;const i=t=>this.edit={...e,...t};return L`<div class="editor">
      <label>${t("name")}<input .value=${e.name} @input=${t=>i({name:me(t)})} /></label>
      <label>${t("interface")}
        <select @change=${t=>i({entry_id:me(t)})}>
          ${this.interfaces.map(t=>L`<option value=${t.id} ?selected=${t.id===e.entry_id}>${t.name}</option>`)}
        </select>
      </label>
      <label>${t("frame")}<input class="mono" placeholder=${t("frame_ph")} .value=${e.frame}
        @input=${t=>i({frame:me(t)})} /></label>
      <label>${t("period_ms")}<input type="number" min="10" .value=${String(e.period_ms)}
        @input=${t=>i({period_ms:Number(me(t))})} /></label>
      <label>${t("count")}<input type="number" min="0" .value=${String(e.count)}
        @input=${t=>i({count:Number(me(t))})} /></label>
      <div class="row">
        <button class="primary" @click=${()=>this.saveDraft()}>${t("save")}</button>
        <button @click=${()=>this.edit=null}>${t("cancel")}</button>
      </div>
      ${this.editError?L`<div class="chip bad" style="white-space:normal">${this.editError}</div>`:K}
    </div>`}render(){const t=this.t,e=this.iface,i=this.whyNot(e),s=t=>this.interfaces.find(e=>e.id===t)?.name??"?";return L`<div class="card">
        <h2>${t("send_title")}</h2>
        <div class="form">
          <label>${t("interface")}
            <select @change=${t=>this.entryId=me(t)}>
              ${this.interfaces.map(e=>L`<option value=${e.id} ?selected=${e.id===this.entryId}>
                ${e.name}${e.can_send?"":` (${t("listen_only")})`}</option>`)}
            </select>
          </label>
          <label class="wide">${t("frame")}
            <input class="mono" placeholder=${t("frame_ph")} .value=${this.frame}
              @input=${t=>this.frame=me(t)}
              @keydown=${t=>"Enter"===t.key&&this.trySend()} />
          </label>
          <label>${t("wait_id")}<input class="mono" placeholder="7E8" .value=${this.waitId}
            @input=${t=>this.waitId=me(t)} /></label>
          <label>${t("wait_ms")}<input type="number" min="0" step="100" .value=${String(this.waitMs)}
            @input=${t=>this.waitMs=Math.max(0,Number(me(t))||0)} /></label>
          <button class="primary" ?disabled=${this.busy||!!i||!this.frame.trim()} @click=${()=>this.trySend()}>
            ${t("send")}
          </button>
        </div>
        <p class="muted">${t("frame_help")}</p>
        ${i&&e?L`<div class="chip warn" style="white-space:normal">${t("cannot_send",{name:e.name,why:i})}</div>`:K}
        ${this.result?L`<div class="result ${this.result.ok?"":"bad"}">${this.result.text}</div>`:K}
      </div>
      <div class="card">
        <div class="row">
          <h2 class="grow">${t("periodic_title")}</h2>
          <button @click=${()=>this.newDraft()}>${t("add")}</button>
        </div>
        <div class="muted">${t("periodic_hint")}</div>
        ${this.renderEditor()}
        ${this.listError?L`<div class="chip bad" style="white-space:normal">${this.listError}</div>`:K}
        ${0===this.periodic.length?L`<div class="empty">${t("periodic_empty")}</div>`:L`<div class="wrap"><table>
              <thead><tr>
                <th>${t("name")}</th><th>${t("interface")}</th><th>${t("frame")}</th><th>${t("period_ms")}</th>
                <th>${t("count")}</th><th></th><th></th>
              </tr></thead>
              <tbody>
                ${this.periodic.map(e=>L`<tr>
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
                    ${e.running?L`<button @click=${()=>this.control(e,"stop")}>${t("stop")}</button>`:L`<button class="primary" @click=${()=>this.control(e,"start")}>${t("start")}</button>`}
                    <button class="link" @click=${()=>{this.editError="",this.edit={id:e.id,name:e.name,entry_id:e.entry_id,frame:e.frame,period_ms:e.period_ms,count:e.count}}}>${t("edit")}</button>
                    <button class="link danger" @click=${()=>this.control(e,"delete")}>${t("delete")}</button>
                  </td>
                </tr>`)}
              </tbody>
            </table></div>`}
      </div>
      ${this.confirming&&e?L`<div class="scrim" @click=${t=>t.target===t.currentTarget&&(this.confirming=!1)}>
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
          </div>`:K}`}}fe.styles=[Rt,o`
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
    `],t([ut({attribute:!1})],fe.prototype,"interfaces",void 0),t([ut({attribute:!1})],fe.prototype,"periodic",void 0),t([ut({attribute:!1})],fe.prototype,"confirmed",void 0),t([ut({attribute:!1})],fe.prototype,"draft",void 0),t([ut({attribute:!1})],fe.prototype,"t",void 0),t([ut({attribute:!1})],fe.prototype,"api",void 0),t([mt()],fe.prototype,"entryId",void 0),t([mt()],fe.prototype,"frame",void 0),t([mt()],fe.prototype,"waitId",void 0),t([mt()],fe.prototype,"waitMs",void 0),t([mt()],fe.prototype,"busy",void 0),t([mt()],fe.prototype,"result",void 0),t([mt()],fe.prototype,"confirming",void 0),t([mt()],fe.prototype,"edit",void 0),t([mt()],fe.prototype,"editError",void 0),t([mt()],fe.prototype,"listError",void 0),St("woow-can-send",fe);const _e=["overview","monitor","analyze","devices","send","capture","activity"];class ve extends lt{constructor(){super(...arguments),this.narrow=!1,this.tab=At("woow_can.tab","overview"),this.interfaces={},this.offline=[],this.periodic={},this.activity=[],this.files=[],this.history={},this.source=At("woow_can.source",""),this.draft=null,this.focusId=null,this.devices={},this.values={},this.signalHistory={},this.charts=At("woow_can.charts",[]),this.templates=[],this.databases=[],this.confirmed=new Set,this.loaded=!1,this.error="",this.t=It("en"),this.api=new xt(()=>this._hass),this.connecting=!1}set hass(t){const e=!this._hass;this._hass=t,e&&(this.t=It(t.locale?.language??t.language??"en"),this.isConnected&&this.connect(),this.requestUpdate())}get hass(){return this._hass}connectedCallback(){super.connectedCallback(),this._hass&&!this.unsubscribe&&this.connect()}disconnectedCallback(){super.disconnectedCallback(),this.unsubscribe?.(),this.unsubscribe=void 0}async connect(){if(!this.connecting&&!this.unsubscribe){this.connecting=!0;try{this.unsubscribe=await this.api.subscribe(t=>this.onEvent(t));const t=await this.api.snapshot();this.interfaces=Object.fromEntries(t.interfaces.map(t=>[t.id,t])),this.offline=t.offline,this.periodic=Object.fromEntries(t.periodic.map(t=>[t.id,t])),this.activity=t.activity,this.devices=Object.fromEntries((t.devices??[]).map(t=>[t.id,t])),this.values=t.values??{},this.templates=t.templates??[],this.databases=t.databases??[],this.source&&(this.source in this.interfaces||t.offline.some(t=>t.id===this.source))||(this.source=this.interfaceList[0]?.id??""),this.loaded=!0,this.error="",this.loadFiles()}catch(t){this.error=kt(t)}finally{this.connecting=!1}}}async loadFiles(){try{const t=await this.api.captures();this.files=t.captures,this.offline=t.offline}catch{}}onEvent(t){switch(t.kind){case"interfaces":{const e={...this.interfaces},i={...this.history};for(const s of t.interfaces)e[s.id]=s,null!=s.load.now&&(i[s.id]=[...i[s.id]??[],s.load.now].slice(-300));for(const i of t.removed)delete e[i];this.interfaces=e,this.history=i,!this.source&&t.interfaces.length&&(this.source=t.interfaces[0].id);break}case"periodic":{const e={...this.periodic};for(const i of t.items)e[i.id]=i;for(const i of t.removed)delete e[i];this.periodic=e;break}case"activity":this.activity=[...t.entries.reverse(),...this.activity].slice(0,500);break;case"captures":this.loadFiles();break;case"devices":{const e={...this.devices};for(const i of t.devices)e[i.id]=i;for(const i of t.removed)delete e[i];this.devices=e;break}case"values":{const e={...this.values},i={...this.signalHistory};for(const[s,a]of Object.entries(t.values)){e[s]={...e[s]??{},...a};for(const[e,r]of Object.entries(a)){if("number"!=typeof r)continue;const a=`${s}|${e}`;i[a]=[...i[a]??[],[t.t,r]].slice(-300)}}this.values=e,this.signalHistory=i;break}case"databases":this.databases=t.databases;break;case"offline":this.offline=t.offline,this.source.startsWith("file:")&&!t.offline.some(t=>t.id===this.source)&&(this.source=this.interfaceList[0]?.id??"")}}get interfaceList(){return Object.values(this.interfaces).sort((t,e)=>t.name.localeCompare(e.name))}setTab(t){this.tab=t,Ct("woow_can.tab",t)}setSource(t){this.source=t,Ct("woow_can.source",t)}toggleMenu(){this.dispatchEvent(new Event("hass-toggle-menu",{bubbles:!0,composed:!0}))}renderTab(){const t=this.interfaceList;switch(this.tab){case"monitor":return L`<woow-can-monitor
          .interfaces=${t}
          .offline=${this.offline}
          .source=${this.source}
          .t=${this.t}
          .api=${this.api}
          @source-changed=${t=>this.setSource(t.detail)}
          @send-frame=${t=>{this.draft={...t.detail,n:(this.draft?.n??0)+1},this.setTab("send")}}
          @analyze-id=${t=>{this.focusId={key:t.detail,n:(this.focusId?.n??0)+1},this.setTab("analyze")}}
        ></woow-can-monitor>`;case"analyze":return L`<woow-can-analyze
          .interfaces=${t}
          .offline=${this.offline}
          .devices=${Object.values(this.devices).sort((t,e)=>t.name.localeCompare(e.name))}
          .source=${this.source}
          .focusId=${this.focusId}
          .t=${this.t}
          .api=${this.api}
        ></woow-can-analyze>`;case"devices":return L`<woow-can-devices
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
          @toggle-chart=${t=>{const e=this.charts.includes(t.detail)?this.charts.filter(e=>e!==t.detail):[...this.charts,t.detail].slice(-8);this.charts=e,Ct("woow_can.charts",e)}}
        ></woow-can-devices>`;case"send":return L`<woow-can-send
          .interfaces=${t}
          .periodic=${Object.values(this.periodic)}
          .confirmed=${this.confirmed}
          .draft=${this.draft}
          .t=${this.t}
          .api=${this.api}
          @confirmed=${t=>this.confirmed=new Set([...this.confirmed,t.detail])}
        ></woow-can-send>`;case"capture":return L`<woow-can-capture
          .interfaces=${t}
          .offline=${this.offline}
          .files=${this.files}
          .t=${this.t}
          .api=${this.api}
          @captures-changed=${()=>this.loadFiles()}
          @open-source=${t=>{this.setSource(t.detail),this.setTab("monitor")}}
        ></woow-can-capture>`;case"activity":return L`<woow-can-activity
          .entries=${this.activity}
          .t=${this.t}
          .portName=${t=>this.interfaces[t]?.name??"?"}
        ></woow-can-activity>`;default:return L`<woow-can-overview
          .interfaces=${t}
          .history=${this.history}
          .t=${this.t}
          @open-monitor=${t=>{this.setSource(t.detail),this.setTab("monitor")}}
        ></woow-can-overview>`}}render(){const t=this.t,e={devices:Object.keys(this.devices).length,send:Object.values(this.periodic).filter(t=>t.running).length,capture:this.files.length};return L`
      <div class="toolbar">
        ${this.narrow?L`<button @click=${this.toggleMenu} aria-label="menu">
              <svg viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d=${"M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z"}></path></svg>
            </button>`:K}
        <div>${t("title")}</div>
      </div>
      <div class="tabs">
        ${_e.map(i=>L`<button class="tab ${this.tab===i?"active":""}" @click=${()=>this.setTab(i)}>
            ${t(`tab_${i}`)}${e[i]?L`<span class="count">${e[i]}</span>`:K}
          </button>`)}
      </div>
      <div class="content">
        ${this.error?L`<div class="card"><div class="chip bad">${t("error",{msg:this.error})}</div></div>`:this.loaded?this.renderTab():L`<div class="empty">${t("loading")}</div>`}
      </div>
    `}}ve.styles=[Rt,o`
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
    `],t([ut({attribute:!1})],ve.prototype,"narrow",void 0),t([ut({attribute:!1})],ve.prototype,"route",void 0),t([ut({attribute:!1})],ve.prototype,"panel",void 0),t([mt()],ve.prototype,"tab",void 0),t([mt()],ve.prototype,"interfaces",void 0),t([mt()],ve.prototype,"offline",void 0),t([mt()],ve.prototype,"periodic",void 0),t([mt()],ve.prototype,"activity",void 0),t([mt()],ve.prototype,"files",void 0),t([mt()],ve.prototype,"history",void 0),t([mt()],ve.prototype,"source",void 0),t([mt()],ve.prototype,"draft",void 0),t([mt()],ve.prototype,"focusId",void 0),t([mt()],ve.prototype,"devices",void 0),t([mt()],ve.prototype,"values",void 0),t([mt()],ve.prototype,"signalHistory",void 0),t([mt()],ve.prototype,"charts",void 0),t([mt()],ve.prototype,"templates",void 0),t([mt()],ve.prototype,"databases",void 0),t([mt()],ve.prototype,"confirmed",void 0),t([mt()],ve.prototype,"loaded",void 0),t([mt()],ve.prototype,"error",void 0),St("woow-can-panel",ve);export{ve as WoowCanPanel};
