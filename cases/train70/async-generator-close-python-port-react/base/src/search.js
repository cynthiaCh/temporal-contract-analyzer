export async function first_match(records,predicate){
 
 while(true){const row=await records.next();if(row.done)return null;if(predicate(row.value)){return row.value;}}
 
}
