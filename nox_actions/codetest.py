# Import built-in modules
import glob
import os

# Import third-party modules
import nox

from nox_actions.utils import MODULE_NAME, THIS_ROOT, build_cpp_extension


def pytest(session: nox.Session) -> None:
    """Run pytest tests with coverage."""
    session.install("-e", ".[dev]")
    test_root = os.path.join(THIS_ROOT, "tests")
    session.run("pytest", f"--cov={MODULE_NAME}",
                "--cov-report=xml:coverage.xml",
                f"--rootdir={test_root}",
                env={"PYTHONPATH": THIS_ROOT.as_posix()})


def coverage(session: nox.Session) -> None:
    """Generate code coverage reports for CI."""
    session.install("-e", ".[dev]")
    test_root = os.path.join(THIS_ROOT, "tests")

    # 运行测试并生成覆盖率报告
    session.run("pytest", f"--cov={MODULE_NAME}",
                "--cov-report=xml:coverage.xml",
                "--cov-report=html:coverage_html",
                f"--rootdir={test_root}",
                env={"PYTHONPATH": THIS_ROOT.as_posix()})

    # 显示覆盖率摘要
    session.run("coverage", "report")


def basic_test(session: nox.Session) -> None:
    """Run a basic test to verify that the package can be imported and used."""
    session.install("-e", ".")

    # Create a simple test script
    test_script = os.path.join(THIS_ROOT, "test_import.py")
    with open(test_script, "w") as f:
        f.write("""
import py_dem_bones
import numpy as np

# Create a simple test function
def test_import():
    print("Successfully imported py_dem_bones")
    # Create a DemBones instance
    db = py_dem_bones.DemBones()
    print("Created DemBones instance")
    # Set some properties
    db.nIters = 10
    print(f"Set nIters to {db.nIters}")
    # Test weights get/set
    test_weights = np.zeros((10, 5), dtype=np.float32)
    test_weights[0, 0] = 1.0
    test_weights[1, 1] = 0.5
    db.set_weights(test_weights)
    retrieved_weights = db.get_weights()
    print(f"Weights shape: {retrieved_weights.shape}")
    print(f"First few values: {retrieved_weights[:2, :2]}")
    print("Basic test completed successfully")

if __name__ == "__main__":
    test_import()
""")

    try:
        # Run the test script
        session.run("python", test_script)
        print("Basic test passed!")
    finally:
        # Clean up
        if os.path.exists(test_script):
            os.remove(test_script)


def find_latest_wheel():
    """Find the latest wheel file in the dist directory."""
    wheels = glob.glob(os.path.join(THIS_ROOT, "dist", "*.whl"))
    if not wheels:
        return None
    return sorted(wheels, key=os.path.getmtime)[-1]


def build_test(session: nox.Session) -> None:
    """Build the package and run unit tests."""
    # 首先构建包
    build_success = build_cpp_extension(session)
    if not build_success:
        session.error("Failed to build C++ extension. Cannot continue with testing.")
        return

    # 获取最新构建的轮子
    latest_wheel = find_latest_wheel()
    if not latest_wheel:
        session.error("No wheel found after build. Cannot continue with testing.")
        return

    session.log(f"Found wheel: {latest_wheel}")

    # 创建一个新的虚拟环境进行测试，避免污染当前环境
    session.log("Creating test environment...")
    with session.chdir(THIS_ROOT):
        # 安装测试依赖和刚构建的轮子
        session.install("pytest", "pytest-cov", "numpy")
        session.install(latest_wheel)

        # 确保测试目录存在
        test_dir = os.path.join(THIS_ROOT, "tests")
        if not os.path.exists(test_dir):
            os.makedirs(test_dir, exist_ok=True)
            # 创建一个简单的测试文件
            test_file = os.path.join(test_dir, "test_import.py")
            if not os.path.exists(test_file):
                with open(test_file, "w") as f:
                    f.write("def test_import():\n")
                    f.write("    import py_dem_bones\n")
                    f.write("    assert py_dem_bones.__version__\n")

        # 运行测试
        session.log("Running tests...")
        env = {"PYTHONPATH": THIS_ROOT.as_posix()}
        session.run("pytest", "tests/", "--cov=py_dem_bones", env=env)


def build_no_test(session: nox.Session) -> None:
    """只构建包，不运行测试，适用于VFX Reference平台环境。"""
    # 仅构建包
    build_success = build_cpp_extension(session)
    if not build_success:
        session.error("Failed to build C++ extension.")
        return
    
    # 获取最新构建的轮子
    latest_wheel = find_latest_wheel()
    if latest_wheel:
        session.log(f"Successfully built wheel: {os.path.basename(latest_wheel)}")
    else:
        session.log("Warning: No wheel found after build.")
