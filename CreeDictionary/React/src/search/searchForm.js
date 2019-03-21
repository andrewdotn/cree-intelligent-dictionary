/*
* SearchForm class
* 
*   Returns Searchform (user input area and submit button)
*   Fetch on SearchWords when click onSubmit(search)
*/

import React from 'react';

import SearchList from './searchList';
import { reset } from './searchList';
import { reset2 } from '../detail/detailWords';

import { searchWord } from '../util';

class SearchForm extends React.Component {
  state = {
    sended: false,
    Words: null,
  };
  constructor(props) {
    super(props);
    this.state = { value: '' };

    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  /* 
  * Used when user inputs word
  * Sets state value to user input
  */
  handleChange(event) {
    this.setState({
      value: event.target.value,
      sended: false,
    });
  }

  /*
  * Used when user submits the word (When search the word)
  * Fetch the user input 
  * Set response to state.Words
  */
  handleSubmit(event) {
    event.preventDefault();
    reset();
    //reset2();
    searchWord(this.state.value).then(response => {
      console.log(response)
      response.json().then(data => {
        //console.log(JSON.stringify(data))
        this.setState({
          sended: true,
          Words: data.words,
        }, () => console.log(this.state))
      })
    });
  }

  /*
  * Used to switch between style of searchform
  */
  getClassNames() {
    let classNames = 'search';
    if (this.state.Words) {
      classNames += 'isTrue';
    }
    return classNames;
  }

  //render
  render() {
    return (
      <div className="card">
          <div className="card-body">
          <form onSubmit={this.handleSubmit.bind(this)} className="form-group">
            <div className="form-row">
              <label> Word:</label>
              <div className="col">
              <input type="text" value={this.state.value} onChange={this.handleChange} className="form-control"/>
              </div>
              <div className="col">
              <button type="submit" className="btn btn-default btn-sm">Search</button>
              </div>
            </div>
          </form>
          </div>
        <SearchList
          Words={this.state.Words}
          sended={this.state.sended}>
        </SearchList>
      </div>
    );
  }
}

export default SearchForm;