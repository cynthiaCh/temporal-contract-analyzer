import React,{createContext,useContext,useState,useImperativeHandle,useEffect,forwardRef} from 'react';
import {Session} from './session.js';
const TransferContext=createContext(null);
const Commands=forwardRef(function Commands(_,ref){const {session,owner}=useContext(TransferContext);useImperativeHandle(ref,()=>({select:f=>session.select(f),retry:()=>session.retry(),hide:()=>session.hide(),dispose:()=>session.dispose(),snapshot:()=>session.snapshot()}),[session]);return <output>{owner.fileId||'closed'}:{owner.attemptId||0}</output>;});
export default forwardRef(function MediaProvider({host},ref){const [owner,setOwner]=useState({}),[session]=useState(()=>new Session(host,setOwner));useEffect(()=>()=>session.dispose(),[session]);return <TransferContext.Provider value={{session,owner}}><section data-business="Editorial media upload"><Commands ref={ref}/></section></TransferContext.Provider>;});
