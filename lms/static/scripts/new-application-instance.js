function addHttp(url) {
  if (url !== '' && !/^(f|ht)tps?:\/\//i.test(url)) {
    url = 'https://' + url;
  }
  return url;
}

function handleSubmit(event, form) {
  if (
    !validateDomain(form.elements.lms_url) ||
    !validateEmail(form.elements.email)
  ) {
    event.preventDefault();
  }
  form.elements.lms_url.value = addHttp(form.elements.lms_url.value);
}

function validateEmail(input) {
  const parent = input.parentElement;
  if (input.value.indexOf('@') === -1) {
    parent.classList.add('has-error');
    parent.getElementsByClassName('error')[0].innerHTML =
      'Please enter a valid email address';
    return false;
  }
  parent.classList.remove('has-error');
  parent.getElementsByClassName('error')[0].innerHTML = '';
  return true;
}

function validateDomain(input) {
  const parent = input.parentElement;
  if (input.value.length === 0) {
    parent.classList.add('has-error');
    parent.getElementsByClassName('error')[0].innerHTML =
      'Please enter a valid domain';
    return false;
  }
  parent.classList.remove('has-error');
  parent.getElementsByClassName('error')[0].innerHTML = '';
  return true;
}

window.newApplicationInstanceForm = {
  handleSubmit,
  validateDomain,
  validateEmail,
};
