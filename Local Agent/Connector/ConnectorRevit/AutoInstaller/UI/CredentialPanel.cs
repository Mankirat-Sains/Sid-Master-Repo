using System;
using System.Windows.Forms;
using Speckle.AutoInstaller.Services;

namespace Speckle.AutoInstaller.UI
{
  public partial class CredentialPanel : UserControl
  {
    private TextBox _txtEmail;
    private TextBox _txtPassword;
    private TextBox _txtServerUrl;
    private Label _lblTitle;
    private Label _lblEmail;
    private Label _lblPassword;
    private Label _lblServerUrl;

    public string Email => _txtEmail.Text.Trim();
    public string Password => _txtPassword.Text;
    public string ServerUrl => _txtServerUrl.Text.Trim();

    public CredentialPanel()
    {
      InitializeComponent();
    }

    private void InitializeComponent()
    {
      this.Size = new System.Drawing.Size(580, 400);
      this.Dock = DockStyle.Fill;

      _lblTitle = new Label
      {
        Text = "Enter your Speckle credentials",
        Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Bold),
        Location = new System.Drawing.Point(20, 20),
        Size = new System.Drawing.Size(500, 30)
      };

      _lblEmail = new Label
      {
        Text = "Email:",
        Location = new System.Drawing.Point(20, 70),
        Size = new System.Drawing.Size(100, 20)
      };

      _txtEmail = new TextBox
      {
        Location = new System.Drawing.Point(130, 68),
        Size = new System.Drawing.Size(400, 20)
      };

      _lblPassword = new Label
      {
        Text = "Password:",
        Location = new System.Drawing.Point(20, 110),
        Size = new System.Drawing.Size(100, 20)
      };

      _txtPassword = new TextBox
      {
        Location = new System.Drawing.Point(130, 108),
        Size = new System.Drawing.Size(400, 20),
        PasswordChar = '*',
        UseSystemPasswordChar = true
      };

      _lblServerUrl = new Label
      {
        Text = "Server URL:",
        Location = new System.Drawing.Point(20, 150),
        Size = new System.Drawing.Size(100, 20)
      };

      _txtServerUrl = new TextBox
      {
        Location = new System.Drawing.Point(130, 148),
        Size = new System.Drawing.Size(400, 20),
        Text = "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com",
        ReadOnly = true,
        BackColor = System.Drawing.SystemColors.Control
      };

      var lblNote = new Label
      {
        Text = "Note: A browser window will open when you click Next. " +
               "Please log in with your Speckle credentials (email and password) in the browser window. " +
               "The email/password fields above are for reference only.",
        Location = new System.Drawing.Point(20, 190),
        Size = new System.Drawing.Size(510, 60),
        ForeColor = System.Drawing.SystemColors.GrayText
      };

      this.Controls.Add(_lblTitle);
      this.Controls.Add(_lblEmail);
      this.Controls.Add(_txtEmail);
      this.Controls.Add(_lblPassword);
      this.Controls.Add(_txtPassword);
      this.Controls.Add(_lblServerUrl);
      this.Controls.Add(_txtServerUrl);
      this.Controls.Add(lblNote);
    }

    public bool ValidateInput()
    {
      if (string.IsNullOrWhiteSpace(Email))
      {
        MessageBox.Show("Please enter your email address.", "Validation Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        _txtEmail.Focus();
        return false;
      }

      if (string.IsNullOrWhiteSpace(Password))
      {
        MessageBox.Show("Please enter your password.", "Validation Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        _txtPassword.Focus();
        return false;
      }

      if (string.IsNullOrWhiteSpace(ServerUrl))
      {
        MessageBox.Show("Please enter the server URL.", "Validation Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        _txtServerUrl.Focus();
        return false;
      }

      if (!Uri.TryCreate(ServerUrl, UriKind.Absolute, out _))
      {
        MessageBox.Show("Please enter a valid server URL.", "Validation Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        _txtServerUrl.Focus();
        return false;
      }

      return true;
    }
  }
}

