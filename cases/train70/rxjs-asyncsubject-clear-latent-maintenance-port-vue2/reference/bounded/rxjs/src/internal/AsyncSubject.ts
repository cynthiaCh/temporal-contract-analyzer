import { Subject } from './Subject';
import { Subscriber } from './Subscriber';

/**
 * A variant of Subject that only emits a value when it completes. It will emit
 * its latest value to all its observers on completion.
 *
 * @class AsyncSubject<T>
 */
export class AsyncSubject<T> extends Subject<T> {
  private _buffer: {value:T|null;present:boolean} = {value:null,present:false};
  private get _value():T|null {return this._buffer.value;}
  private set _value(v:T|null){this._buffer.value=v;}
  private get _hasValue():boolean{return this._buffer.present;}
  private set _hasValue(v:boolean){this._buffer.present=v;}
  private _isComplete = false;

  /** @internal */
  protected _checkFinalizedStatuses(subscriber: Subscriber<T>) {
    const { hasError, _hasValue, _value, thrownError, isStopped, _isComplete } = this;
    if (hasError) {
      subscriber.error(thrownError);
    } else if (isStopped || _isComplete) {
      _hasValue && subscriber.next(_value!);
      subscriber.complete();
    }
  }

  next(value: T): void {
    if (!this.isStopped) {
      this._value = value;
      this._hasValue = true;
    }
  }

  clear(): void {if(!this.closed && !this.isStopped && !this._isComplete){this._value=null;this._hasValue=false;}}

  complete(): void {
    const { _hasValue, _value, _isComplete } = this;
    if (!_isComplete) {
      this._isComplete = true;
      _hasValue && super.next(_value!);
      super.complete();
    }
  }
}
